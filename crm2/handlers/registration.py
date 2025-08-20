# crm2/handlers/registration.py
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
#  МОДУЛЬ: crm2/handlers/registration.py
#  НАЗНАЧЕНИЕ:
#    Пошаговая регистрация пользователей (FSM) в CRM2 на aiogram 3.13.1.
#    Собирает ФИО → ник → пароль → подтверждение → выбор потока (или «Без потока»).
#    Проверяет уникальность ника; при занятости — сбрасывает FSM и предлагает
#    начать регистрацию заново, чтобы избежать путаницы.
#
#  ОСОБЕННОСТИ:
#    • Состояния FSM: full_name, nickname, password, password_confirm, cohort.
#    • Запуск регистрации по кнопке «🆕 Зарегистрироваться», по фразе «зарегистр…»
#      и по команде /register.
#    • Выбор потока из таблицы cohorts + опция «Без потока» (cohort_id=NULL).
#    • Сохранение в таблицу users через UPDATE по telegram_id (роль → 'user').
#    • Пароли хэшируются bcrypt (passlib); логика last_seen ведётся отдельно.
#
#  ХРАНИЛИЩЕ ДАННЫХ:
#    • SQLite: путь берётся из crm2.db.sqlite.DB_PATH — единая точка для проекта.
#
#  ЗАВИСИМОСТИ:
#    aiogram==3.13.1, passlib[bcrypt], sqlite3 (stdlib), Python 3.12+.
#
#  ПРИМЕЧАНИЯ:
#    • В схеме users заданы UNIQUE(telegram_id) и UNIQUE(nickname):
#      один Telegram-ID = одна учётная запись; дублей ников не допускаем.
#    • При повторной регистрации уже зарегистрированного пользователя FSM
#      перенаправляет к «Войти», чтобы не смешивать учётные данные.
# ---------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
#  МОДУЛЬ: crm2/handlers/registration.py
#  НАЗНАЧЕНИЕ:
#    Пошаговая регистрация пользователей (FSM) в CRM2 на aiogram 3.13.1:
#    ФИО → ник → пароль → подтверждение → выбор потока (или «Без потока»).
#    Ник уникален; запись в БД происходит только в финале (UPDATE по telegram_id).
#
#  ОТЛАДКА:
#    DEBUG_MODE=True (только для ADMIN_TG_ID) включает кнопку
#    «Отладка: ввести Telegram ID» — позволяет регистрировать тестовых пользователей
#    с подменой telegram_id. В бою выключить и удалить хэндлеры отладки.
# ---------------------------------------------------------------------------

from __future__ import annotations

import sqlite3
from passlib.hash import bcrypt

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from crm2.db.sqlite import DB_PATH

router = Router()

# =============================== Отладка ===============================
# ⚠️ В бою ОБЯЗАТЕЛЬНО: DEBUG_MODE = False и удалить «debug_*» хэндлеры.
DEBUG_MODE = True
ADMIN_TG_ID = 448124106
# ======================================================================

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
def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


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


# ================ handlers =====================
# Старт регистрации — ловим кнопку/текст/команду
@router.message(F.text == "🆕 Зарегистрироваться")
@router.message(F.text.func(lambda t: isinstance(t, str) and "зарегистр" in t.lower()))
@router.message(Command("register"))
async def start_registration(message: Message, state: FSMContext):
    await state.clear()

    # Если юзер уже есть — не пускаем регистрироваться повторно (кроме отладки)
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

    # Режим отладки — только для ADMIN_TG_ID: предложим подмену telegram_id
    if DEBUG_MODE and message.from_user.id == ADMIN_TG_ID:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Отладка: ввести Telegram ID")],
                [KeyboardButton(text="Продолжить без подмены ID")],
            ],
            resize_keyboard=True,
        )
        await message.answer(
            "Режим отладки: можно подменить Telegram ID для тестовой регистрации.\n"
            "Выберите действие:",
            reply_markup=kb,
        )
        return

    # Обычный путь — начинаем сбор данных
    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


# ---------- Отладка: подмена telegram_id ----------
@router.message(F.text == "Отладка: ввести Telegram ID")
async def debug_set_tg_id(message: Message, state: FSMContext):
    if not (DEBUG_MODE and message.from_user.id == ADMIN_TG_ID):
        await message.answer("Эта функция недоступна.", reply_markup=ReplyKeyboardRemove())
        return
    await state.set_state(RegistrationFSM.debug_tg_id)
    await message.answer("Введите желаемый Telegram ID (число):", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == "Продолжить без подмены ID")
async def debug_continue_no_fake(message: Message, state: FSMContext):
    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


@router.message(RegistrationFSM.debug_tg_id)
async def debug_tg_id_entered(message: Message, state: FSMContext):
    if not (DEBUG_MODE and message.from_user.id == ADMIN_TG_ID):
        await message.answer("Эта функция недоступна.", reply_markup=ReplyKeyboardRemove())
        return
    try:
        fake_id = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите корректное число (Telegram ID):")
        return

    await state.update_data(fake_telegram_id=fake_id)
    await state.set_state(RegistrationFSM.full_name)
    await message.answer("✅ Принято. Теперь введите ваше ФИО:")
# ---------- конец блока отладки ----------


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
        # При занятости ника — сбрасываем FSM и отправляем начать заново
        await state.clear()
        await message.answer(
            "❌ Такой ник уже занят.\n"
            "Пожалуйста, начните регистрацию заново: /start → «🆕 Зарегистрироваться».",
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

    # Переходим к выбору потока
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
    password_hash = bcrypt.hash(data["password"])
    tg_id = resolve_telegram_id(message, data)

    # ВАЖНО: строка гостя создана ранее (ensure_user на /start),
    # здесь мы обновляем её финальными полями и ролью 'user'
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
               SET full_name     = ?,
                   nickname      = ?,
                   password_hash = ?,
                   role          = 'user',
                   cohort_id     = ?
             WHERE telegram_id   = ?
            """,
            (data["full_name"], data["nickname"], password_hash, cohort_id, tg_id),
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
    return

@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Регистрация отменена. Нажмите /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )
