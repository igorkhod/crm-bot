from __future__ import annotations

import sqlite3
import re
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
from crm2.handlers.consent import has_consent, consent_kb, CONSENT_TEXT

router = Router()
DEBUG_MODE = False

NO_COHORT = "Без потока"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegistrationFSM(StatesGroup):
    consent = State()
    full_name = State()
    nickname = State()
    password = State()
    password_confirm = State()
    phone = State()
    email = State()
    cohort = State()
    debug_tg_id = State()


def _ensure_min_schema() -> None:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                nickname TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                phone TEXT,
                email TEXT,
                events TEXT,
                participants TEXT,
                cohort_id INTEGER
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS participants(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                cohort_id INTEGER,
                cohort_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS cohorts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            '''
        )
        # Базовые варианты потоков
        cur.execute("INSERT OR IGNORE INTO cohorts(name) VALUES (?)", ("09.2023",))
        cur.execute("INSERT OR IGNORE INTO cohorts(name) VALUES (?)", ("04.2025",))
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
    return rows


def nickname_exists(nickname: str) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE nickname = ?", (nickname,))
        return cur.fetchone() is not None


def resolve_telegram_id(message: Message, data: dict) -> int:
    if DEBUG_MODE and data.get("fake_telegram_id"):
        return int(data["fake_telegram_id"])
    return message.from_user.id


def _is_reg(text: str | None) -> bool:
    if not text:
        return False
    t = ''.join(ch for ch in text.casefold() if ch.isalnum() or ch.isspace()).strip()
    return t.startswith("регист") or t.startswith("зарегистр") or "register" in t


# ==== start registration ====
@router.message(StateFilter(None), Command("register"))
@router.message(StateFilter(None), F.text.func(_is_reg))
@router.message(StateFilter(None), F.text.in_({"🆕 Зарегистрироваться", "📝 Регистрация"}))
@router.message(StateFilter(None), F.text.func(lambda t: isinstance(t, str) and any(s in t.lower() for s in ("регист", "зарегистр"))))
async def start_registration(message: Message, state: FSMContext):
    _ensure_min_schema()

    if not has_consent(message.from_user.id):
        await state.set_state(RegistrationFSM.consent)
        await message.answer(CONSENT_TEXT, reply_markup=consent_kb())
        return

    await state.clear()

    already = get_user_by_tg_id(message.from_user.id)
    if already and not DEBUG_MODE:
        kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔐 Войти")]], resize_keyboard=True)
        await message.answer("Вы уже зарегистрированы. Нажмите «🔐 Войти» и введите пароль.", reply_markup=kb)
        return

    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


@router.callback_query(StateFilter(None), F.data.startswith("registration:"))
async def registration_start_cb(cb: CallbackQuery, state: FSMContext):
    _ensure_min_schema()

    if not has_consent(cb.from_user.id):
        await state.set_state(RegistrationFSM.consent)
        await cb.answer()
        await cb.message.answer(CONSENT_TEXT, reply_markup=consent_kb())
        return

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
        await message.answer("❌ Такой ник уже занят. Начните регистрацию заново: /start → «Регистрация».", reply_markup=ReplyKeyboardRemove())
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

    # Переходим к телефону
    await state.set_state(RegistrationFSM.phone)
    await message.answer("Введите ваш телефон (например, +7 900 123-45-67):", reply_markup=ReplyKeyboardRemove())


@router.message(RegistrationFSM.phone)
async def reg_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10:
        await message.answer("Похоже, телефон некорректный. Введите ещё раз, например: +7 900 123-45-67.")
        return
    await state.update_data(phone=phone)
    await state.set_state(RegistrationFSM.email)
    await message.answer("Введите e-mail:", reply_markup=ReplyKeyboardRemove())


@router.message(RegistrationFSM.email)
async def reg_email(message: Message, state: FSMContext):
    email = (message.text or "").strip()
    if not EMAIL_RE.match(email):
        await message.answer("Похоже, e-mail некорректный. Введите ещё раз.")
        return
    await state.update_data(email=email)

    # Кнопки потоков в одну строку
    await state.set_state(RegistrationFSM.cohort)
    cohorts = get_cohorts()
    row = [KeyboardButton(text=name) for _, name in cohorts] + [KeyboardButton(text=NO_COHORT)]
    kb = ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True, input_field_placeholder="Выберите поток")
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
        # UPDATE — 7 значений
        cur.execute(
            '''
            UPDATE users
            SET full_name = ?,
                nickname  = ?,
                password  = ?,
                cohort_id = ?,
                role      = COALESCE(role, 'user'),
                phone     = ?,
                email     = ?
            WHERE telegram_id = ?
            ''',
            (data["full_name"], data["nickname"], password_hash, cohort_id, data.get("phone"), data.get("email"), tg_id),
        )

        if cur.rowcount == 0:
            # INSERT — если не обновили
            cur.execute(
                '''
                INSERT INTO users
                    (telegram_id, username, nickname, password, full_name, role, cohort_id, phone, email)
                VALUES (?, ?, ?, ?, ?, 'user', ?, ?, ?)
                ''',
                (tg_id, data["nickname"], data["nickname"], password_hash, data["full_name"],
                 cohort_id, data.get("phone"), data.get("email")),
            )

        # Привязка к потоку (upsert по user_id)
        cur.execute(
            '''
            INSERT INTO participants (user_id, cohort_id)
            SELECT id, ? FROM users WHERE telegram_id = ?
            ON CONFLICT(user_id) DO UPDATE SET cohort_id = excluded.cohort_id
            ''',
            (cohort_id, tg_id),
        )
        conn.commit()

    await state.clear()
    kb_login = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔐 Войти")]], resize_keyboard=True)
    await message.answer(
        f"✅ Регистрация завершена!\n"
        f"Добро пожаловать, {data['full_name']}.\n"
        f"Поток: {cohort_name}\n\n"
        f"Теперь вы можете войти в систему:",
        reply_markup=kb_login,
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Регистрация отменена. Нажмите /start, чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
