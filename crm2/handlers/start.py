# crm2/handlers/start.py

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from crm2.handlers.consent import has_consent, consent_kb, CONSENT_TEXT

import sqlite3
from crm2.db.sqlite import DB_PATH
from crm2.keyboards import guest_start_kb, role_kb
from crm2.handlers_schedule import show_info_menu
from crm2.keyboards import guest_start_kb


router = Router(name="start")

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # --- проверяем пользователя в БД и его роль ---
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT role FROM users WHERE telegram_id = ? LIMIT 1",
            (message.from_user.id,),
        ).fetchone()

    is_new = row is None
    role = (row["role"] if row and row["role"] else "curious")

    # --- новые пользователи: поэтическое приветствие + явная подсказка ---
    if is_new:
        text = (
            "🌌 *Добро пожаловать в Psytech!*\n\n"
            "Здесь начинается путь — от рассеянности к ясности, "
            "от суеты к собранности, от привычного к свободе.\n\n"
            "Мы бережно соединяем практики внимания и воли, чтобы ты смог "
            "раскрыть внутренний источник силы и устойчивости.\n\n"
            "Нажмите *«Войти»* или *«Регистрация»*, чтобы продолжить."
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=guest_start_kb())
        return

    # --- для зарегистрированных: проверка согласия (если требуется) ---
    if not has_consent(message.from_user.id):
        await message.answer(CONSENT_TEXT, reply_markup=consent_kb())
        return

    # --- зарегистрированных кидаем сразу в главное меню и открываем подменю расписания ---
    await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))
    # сразу показываем подменю расписания, чтобы было «с расписанием»
    await show_info_menu(message)
