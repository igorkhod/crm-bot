# crm2/handlers/admin_db_doctor.py
import sqlite3
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from crm2.db.sqlite import DB_PATH

router = Router(name="admin_db_doctor")

# Главное меню DB Doctor
@router.message(F.text == "🩺 DB Doctor")
async def db_doctor_menu(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Структура БД"), KeyboardButton(text="🛠 Исправить sessions")],
            [KeyboardButton(text="📂 Индексы"), KeyboardButton(text="↩️ Главное меню")],
        ],
        resize_keyboard=True,
    )
    await message.answer("🩺 DB Doctor — выбор действия:", reply_markup=kb)


@router.message(F.text == "📊 Структура БД")
async def show_structure(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cols = con.execute("PRAGMA table_info(sessions);").fetchall()
    text = "📊 *sessions*:\n" + "\n".join(
        f"• {c['cid']} — {c['name']} ({c['type']})" for c in cols
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "🛠 Исправить sessions")
async def fix_sessions(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        # cohort_id
        cols = {c[1] for c in cur.execute("PRAGMA table_info(sessions);")}
        if "cohort_id" not in cols:
            cur.execute("ALTER TABLE sessions ADD COLUMN cohort_id INTEGER;")
        if "cohort_id" in cols:
            cur.execute(
                "UPDATE sessions SET cohort_id = cohort_id WHERE cohort_id IS NULL;"
            )
        # индексы
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_cohort_start ON sessions(cohort_id, start_date);"
        )
        cur.execute("DROP INDEX IF EXISTS idx_sessions_cohort_start;")
        con.commit()
    await message.answer("✅ Таблица *sessions* исправлена.", parse_mode="Markdown")


@router.message(F.text == "📂 Индексы")
async def show_indexes(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("PRAGMA index_list(sessions);").fetchall()
    if not rows:
        await message.answer("Нет индексов в таблице sessions.")
    else:
        text = "📂 *Индексы sessions*:\n" + "\n".join(str(r) for r in rows)
        await message.answer(text, parse_mode="Markdown")
