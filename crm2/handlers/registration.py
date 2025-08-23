# crm2/handlers/registration.py
from __future__ import annotations

import sqlite3
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from passlib.hash import bcrypt

from crm2.db.core import get_db_connection
from crm2.db.sqlite import DB_PATH  # noqa: F401  # оставляем для совместимости/диагностики

router = Router()
DEBUG_MODE = False  # в проде держать False

NO_COHORT = "Без потока"


# ===================== FSM =====================
class RegistrationFSM(StatesGroup):
    full_name = State()
    nickname = State()
    password = State()
    password_confirm = State()
    cohort = State()
    debug_tg_id = State()  # только для отладки


# ================== helpers ====================
def _ensure_min_schema() -> None:
    """
    Создаёт необходимые таблицы (users, cohorts), если их ещё нет.
    Это защищает первый запуск на Render от падения 'no such table: users'.
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER UNIQUE,
                username     TEXT,
                nickname     TEXT UNIQUE,
                password     TEXT,
                full_name    TEXT,
                role         TEXT DEFAULT 'user',
                phone        TEXT,
                email        TEXT,
                events       TEXT,
                participants TEXT,
                cohort_id    INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cohorts (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        conn.commit()


def get_user_by_tg_id(tg_id: int) -> dict | None:
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,))
        row = cur.fetchone()
    return dict(row) if row else None


def get_cohorts() -> list[tuple[int, str]]:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cohorts ORDER BY id")
        rows = cur.fetchall()
    return rows  # [(id, name), ...]


def nickname_exists(nickname: str) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE nickname = ?", (nickname,))
        return cur.fetchone() is not None


def resolve_telegram_id(message: Message, data: dict) -> int:
    """
    Возвращает telegram_id для записи в БД:
    • если DEBUG_MODE и в состоянии есть fake_telegram_id — берём его;
    • иначе — реальный message.from_user.id.
    """
    if DEBUG_MODE and data.get("fake_telegram_id"):
        return int(data["fake_telegram_id"])
    return message.from_user.id


def _is_reg(text: str | None) -> bool:
    """Мягкий фильтр: ловит 'регистрация', '✏️ Регистрация', 'зарегистрироваться' и т.п."""
    if not text:
        return False
    t = ''.join(ch for ch in text.casefold() if ch.isalnum() or ch.isspace()).strip()
    return t.startswith("регист") or t.startswith("зарегистр") or "register" in t


# ================ handlers =====================
# Старт регистрации — ловим кнопку/текст/команду
@router.message(StateFilter(None), Command("register"))
@router.message(StateFilter(None), F.text.func(_is_reg))
async def start_registration(message: Message, state: FSMContext):
    _ensure_min_schema()  # защищаемся от 'no such table' на первом старте
    await state.clear()

    already = get_user_by_tg_id(message.from_user.id)
    if already and not DEBUG_MODE:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔐 Войти")]],
            resize_keyboard=True,
        )
        await message.answer(
            "Вы уже зарегистрированы. Нажмите «🔐 Войти» и введите пароль.",
            reply_markup=kb,
        )
        return

    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


# На будущее: если сделаешь inline-кнопку с callback_data="registration:start"
@router.callback_query(StateFilter(None), F.data.startswith("registration:"))
async def registration_start_cb(cb: CallbackQuery, state: FSMContext):
    _ensure_min_schema()
    await cb.answer()
    await state.clear()
    await state.set_state(RegistrationFSM.full_name)
    await cb.message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


@router.message(RegistrationFSM.full_name)
async def reg_full_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()
    if len(full_name) < 3:
        await message.answer("Слишком коротко. Введите ФИО полностью:")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationFSM.nickname)
    await message.answer("Придумайте никнейм для входа:")


@router.message(RegistrationFSM.nickname)
async def reg_nickname(message: Message, state: FSMContext):
    nickname = (message.text or "").strip()
    if len(nickname) < 3:
        await message.answer("Ник слишком короткий. Введите другой:")
        return

    if nickname_exists(nickname):
        await state.clear()
        await message.answer(
            "❌ Такой ник уже занят.\n"
            "Пожалуйста, начните регистрацию заново: /start → «Регистрация».",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.update_data(nickname=nickname)
    await state.set_state(RegistrationFSM.password)
    await message.answer("Введите пароль:")


@router.message(RegistrationFSM.password)
async def reg_password(message: Message, state: FSMContext):
    pwd = (message.text or "").strip()
    if len(pwd) < 6:
        await message.answer("Пароль должен быть не короче 6 символов. Введите снова:")
        return
    await state.update_data(password=pwd)
    await state.set_state(RegistrationFSM.password_confirm)
    await message.answer("Повторите пароль:")


@router.message(RegistrationFSM.password_confirm)
async def reg_password_confirm(message: Message, state: FSMContext):
    confirm = (message.text or "").strip()
    data = await state.get_data()
    if confirm != data.get("password", ""):
        await message.answer("❌ Пароли не совпадают. Введите пароль ещё раз:")
        await state.set_state(RegistrationFSM.password)
        return

    await state.set_state(RegistrationFSM.cohort)

    cohorts = get_cohorts()
    rows: list[list[KeyboardButton]] = [[KeyboardButton(text=name)] for _, name in cohorts]
    rows.append([KeyboardButton(text=NO_COHORT)])

    kb = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    await message.answer("Выберите поток:", reply_markup=kb)


@router.message(RegistrationFSM.cohort)
async def reg_cohort(message: Message, state: FSMContext):
    choice = (message.text or "").strip()

    cohorts = get_cohorts()
    name_to_id = {name: cid for cid, name in cohorts}

    if choice.lower() == NO_COHORT.lower():
        cohort_id = None
        cohort_name = NO_COHORT
    elif choice in name_to_id:
        cohort_id = name_to_id[choice]
        cohort_name = choice
    else:
        await message.answer("❌ Такого варианта нет. Выберите из списка.")
        return

    data = await state.get_data()
    tg_id = resolve_telegram_id(message, data)
    password_hash = bcrypt.hash(data["password"])

    with get_db_connection() as conn:
        cur = conn.cursor()

        # сначала пробуем обновить существующую запись по telegram_id
        cur.execute(
            """
            UPDATE users
            SET full_name = ?,
                nickname  = ?,
                password  = ?,
                cohort_id = ?,
                role      = COALESCE(role, 'user')
            WHERE telegram_id = ?
            """,
            (data["full_name"], data["nickname"], password_hash, cohort_id, tg_id),
        )

        # если не зацепили ни одной строки — создаём новую
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO users (telegram_id, username, nickname, password, full_name, role, cohort_id)
                VALUES (?, ?, ?, ?, ?, 'user', ?)
                """,
                (tg_id, data["nickname"], data["nickname"], password_hash, data["full_name"], cohort_id),
            )
        conn.commit()

    await state.clear()
    text = (
        f"✅ Регистрация завершена!\n"
        f"Добро пожаловать, {data['full_name']}.\n"
        f"Поток: {cohort_name}\n\n"
        f"Теперь вы можете войти в систему:"
    )
    kb_login = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔐 Войти")]],
        resize_keyboard=True,
    )
    await message.answer(text, reply_markup=kb_login)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Регистрация отменена. Нажмите /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )
