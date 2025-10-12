# crm2/handlers/admin_db_doctor.py
# Назначение: Мини-панель для диагностики и ремонта базы данных (только для админов)
# Функции:
# - show_menu - Показ меню DB Doctor с кнопками действий
# - action_sessions_info - Показ структуры таблицы sessions
# - action_fix_sessions - Исправление структуры таблицы sessions (добавление cohort_id)
# - action_indexes - Показ индексов таблицы sessions
# - action_become_guest - Удаление пользователя из базы (стать гостем)
# - action_become_user2 - Изменение роли пользователя на user с когортой 2
# - back_to_main - Возврат в главное меню
"""
🩺 DB Doctor — мини-панель для проверки/ремонта БД.
Используем общий коннектор БД, чтобы работать ровно с той же базой, что и весь бот.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from crm2.db.users import get_db_connection   # ВАЖНО: единая точка подключения
from crm2.db import auto_migrate
import sqlite3

router = Router(name="admin_db_doctor")

# Тексты кнопок
BTN_STRUCT = "📊 Структура БД"
BTN_FIX = "🛠 Исправить sessions"
BTN_INDEXES = "📂 Индексы"
BTN_BACK = "↩️ Главное меню"
BTN_BECOME_GUEST = "🙈 Стать гостем"
BTN_BECOME_USER2 = "👤 Стать user поток 2"


async def show_menu(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STRUCT), KeyboardButton(text=BTN_FIX)],
            [KeyboardButton(text=BTN_INDEXES), KeyboardButton(text=BTN_BACK)],
            [KeyboardButton(text=BTN_BECOME_GUEST), KeyboardButton(text=BTN_BECOME_USER2)],
        ],
        resize_keyboard=True,
    )
    await message.answer("🩺 DB Doctor — выберите действие:", reply_markup=kb)


# ---------- 📊 Структура БД ----------
@router.message(F.text.startswith("📊"))
@router.message(F.text.contains("труктур"))
@router.message(Command("db_sessions_info"))
async def action_sessions_info(message: Message):
    try:
        with get_db_connection() as con:
            con.row_factory = sqlite3.Row
            cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions';")
            t = cur.fetchone()
            if not t:
                await message.answer("❌ Таблица <b>sessions</b> отсутствует.")
                return

            cur = con.execute("PRAGMA table_info(sessions);")
            cols = cur.fetchall()
            cur = con.execute("SELECT COUNT(*) AS c FROM sessions;")
            count = cur.fetchone()["c"]

        lines = ["📊 Таблица <b>sessions</b>:"]
        for col in cols:
            # PRAGMA table_info: (cid, name, type, notnull, dflt_value, pk)
            lines.append(f"- {col['name']} ({col['type']})")
        lines.append(f"\nВсего записей: <b>{count}</b>")
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
        with get_db_connection() as con:
            auto_migrate.ensure_topics_and_session_days(con)
            con.commit()
        await message.answer("✅ Готово: <b>cohort_id</b> добавлен/обновлён, данные перенесены, индекс создан.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# ---------- 📂 Индексы ----------
@router.message(F.text.startswith("📂"))
@router.message(F.text.contains("ндекс"))
@router.message(Command("db_indexes"))
async def action_indexes(message: Message):
    try:
        with get_db_connection() as con:
            con.row_factory = sqlite3.Row
            cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions';")
            t = cur.fetchone()
            if not t:
                await message.answer("❌ Таблица <b>sessions</b> отсутствует.")
                return

            cur = con.execute("PRAGMA index_list('sessions');")
            idx = cur.fetchall()

        if not idx:
            await message.answer("❌ Индексы отсутствуют.")
            return

        lines = ["📂 Индексы таблицы <b>sessions</b>:"]
        for row in idx:
            # (seq, name, unique, origin, partial) — обращаемся по индексам
            lines.append(f"- {row[1]} (unique={row[2]})")
        await message.answer("\n".join(lines))
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# ---------- 🙈 Стать гостем ----------
@router.message(F.text == BTN_BECOME_GUEST)
async def action_become_guest(message: Message):
    try:
        with get_db_connection() as con:
            con.execute("DELETE FROM users WHERE telegram_id=?;", (message.from_user.id,))
            con.commit()
        await message.answer("✅ Вы полностью удалены из базы (гость).")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# ---------- 👤 Стать user поток 2 ----------
@router.message(F.text == BTN_BECOME_USER2)
async def action_become_user2(message: Message):
    try:
        tg_id = message.from_user.id
        with get_db_connection() as con:
            # Создаём минимальную запись, если не было (после «Стать гостем»)
            con.execute(
                "INSERT OR IGNORE INTO users (telegram_id, role, full_name) VALUES (?, 'user', '');",
                (tg_id,),
            )
            con.execute(
                "UPDATE users SET role='user', cohort_id=2 WHERE telegram_id=?;",
                (tg_id,),
            )
            con.commit()
        await message.answer("✅ Ваша роль изменена: user, поток = 2.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# ---------- ↩️ Главное меню ----------
@router.message(F.text == BTN_BACK)
async def back_to_main(message: Message):
    from crm2.keyboards import role_kb
    from crm2.db.users import get_user_by_tg

    user = get_user_by_tg(message.from_user.id)
    role = (user or {}).get("role", "user")
    await message.answer("Главное меню:", reply_markup=role_kb(role))
