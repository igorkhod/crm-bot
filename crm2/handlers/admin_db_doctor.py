# crm2/handlers/admin_db_doctor.py
"""
Хендлеры раздела 🩺 DB Doctor.
Смотрим состояние БД и чиним типовые проблемы.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import sqlite3
from pathlib import Path
from crm2.db import auto_migrate

router = Router(name="admin_db_doctor")

# Тексты кнопок
BTN_STRUCT = "📊 Структура БД"
BTN_FIX = "🛠 Исправить sessions"
BTN_INDEXES = "📂 Индексы"
BTN_BACK = "↩️ Главное меню"

DB_PATH = Path("crm.db")   # поправь путь, если у тебя другой


# ---------- Меню DB Doctor ----------
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


# ---------- 📊 Структура БД ----------
# Три декоратора на одну функцию: 2 по тексту, 1 по команде
@router.message(F.text.startswith("📊"))
@router.message(F.text.contains("труктур"))
@router.message(Command("db_sessions_info"))
async def action_sessions_info(message: Message):
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("PRAGMA table_info(sessions);")
        cols = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM sessions;")
        count = cur.fetchone()[0]
        con.close()

        lines = [ "📊 Таблица sessions:" ]
        for col in cols:
            lines.append(f"- {col[1]} ({col[2]})")
        lines.append(f"\nВсего записей: {count}")
        await message.answer("\n".join(lines))
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# ---------- 🛠 Исправить sessions ----------
@router.message(F.text.startswith("🛠"))
@router.message(F.text.contains("править"))
@router.message(F.text.contains("sessions"))
@router.message(Command("db_fix_cohort"))
async def action_fix_sessions(message: Message):
    try:
        con = sqlite3.connect(DB_PATH)
        auto_migrate.ensure_topics_and_session_days(con)
        con.close()
        await message.answer("✅ Готово: cohort_id добавлен/обновлён, данные перенесены, индекс создан.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# ---------- 📂 Индексы ----------
@router.message(F.text.startswith("📂"))
@router.message(F.text.contains("ндекс"))
@router.message(Command("db_indexes"))
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

        lines = ["📂 Индексы таблицы sessions:"]
        for row in idx:
            # row: (seq, name, unique, origin, partial)
            lines.append(f"- {row[1]} (unique={row[2]})")
        await message.answer("\n".join(lines))
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# ---------- ↩️ Главное меню ----------
@router.message(F.text == BTN_BACK)
async def back_to_main(message: Message):
    from crm2.keyboards import role_kb
    from crm2.db.users import get_user_by_tg

    user = await get_user_by_tg(message.from_user.id)
    role = (user or {}).get("role", "user")
    await message.answer("Главное меню:", reply_markup=role_kb(role))
