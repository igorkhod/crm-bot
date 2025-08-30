# crm2/handlers/admin_db_doctor.py
"""
Хендлеры раздела 🩺 DB Doctor
Позволяют администратору смотреть состояние базы и чинить ошибки.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from crm2.db import auto_migrate
import sqlite3
from pathlib import Path

router = Router(name="admin_db_doctor")

# --- Кнопки ---
BTN_STRUCT = "📊 Структура БД"
BTN_FIX = "🛠 Исправить sessions"
BTN_INDEXES = "📂 Индексы"
BTN_BACK = "↩️ Главное меню"

DB_PATH = Path("crm.db")  # если у тебя путь другой, поправь


def _txt(t: str) -> str:
    return (t or "").strip().lower()


# --- Главное меню DB Doctor ---
async def show_menu(message: Message):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STRUCT)],
            [KeyboardButton(text=BTN_FIX)],
            [KeyboardButton(text=BTN_INDEXES)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True
    )
    await message.answer("🩺 DB Doctor — выберите действие:", reply_markup=kb)


# --- Структура БД ---
@router.message(
    F.text.startswith("📊") | F.text.contains("труктур") | Command("db_sessions_info")
)
async def action_sessions_info(message: Message):
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("PRAGMA table_info(sessions);")
        cols = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM sessions;")
        count = cur.fetchone()[0]
        con.close()

        text = "📊 Таблица sessions:\n"
        for col in cols:
            text += f"- {col[1]} ({col[2]})\n"
        text += f"\nВсего записей: {count}"
        await message.answer(text)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# --- Исправление sessions ---
@router.message(
    F.text.startswith("🛠") | F.text.contains("sessions") | Command("db_fix_cohort")
)
async def action_fix_sessions(message: Message):
    try:
        con = sqlite3.connect(DB_PATH)
        auto_migrate.ensure_topics_and_session_days(con)
        con.close()
        await message.answer("✅ Готово: cohort_id добавлен/обновлён, данные перенесены, индекс создан.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# --- Индексы ---
@router.message(
    F.text.startswith("📂") | F.text.contains("ндекс") | Command("db_indexes")
)
async def action_indexes(message: Message):
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("PRAGMA index_list(sessions);")
        idx = cur.fetchall()
        con.close()

        if not idx:
            await message.answer("❌ Индексы отсутствуют.")
            return

        text = "📂 Индексы таблицы sessions:\n"
        for row in idx:
            text += f"- {row[1]} (unique={row[2]})\n"
        await message.answer(text)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# --- Возврат в главное меню ---
@router.message(F.text == BTN_BACK)
async def back_to_main(message: Message):
    from crm2.keyboards import role_kb
    from crm2.db.users import get_user_by_tg

    user = await get_user_by_tg(message.from_user.id)
    role = user["role"] if user else "user"
    await message.answer("Главное меню:", reply_markup=role_kb(role))
