# crm2/handlers/admin_db_doctor.py
from __future__ import annotations

import sqlite3
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from crm2.db.sqlite import DB_PATH

router = Router(name="admin_db_doctor")


# --- Публичная функция, которую вызывает admin/panel.py -----------------------
async def show_menu(message: Message) -> None:
    """
    Рисует главное меню DB Doctor (кнопочная клавиатура).
    Вызывается из admin/panel.py -> admin_dbdoctor_entry(...)
    """
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Структура БД"), KeyboardButton(text="🛠 Исправить sessions")],
            [KeyboardButton(text="📂 Индексы"), KeyboardButton(text="↩️ Главное меню")],
        ],
        resize_keyboard=True,
    )
    await message.answer("🩺 DB Doctor — выбор действия:", reply_markup=kb)


# --- Дублируем вход по текстовой кнопке, если зайдут напрямую -----------------
@router.message(F.text == "🩺 DB Doctor")
async def db_doctor_menu(message: Message):
    await show_menu(message)


# --- Текстовые команды на всякий случай ---------------------------------------
@router.message(Command("db_sessions_info"))
async def db_sessions_info_cmd(message: Message):
    await db_sessions_info(message)

@router.message(Command("db_fix_cohort"))
async def db_fix_cohort_cmd(message: Message):
    await db_fix_cohort(message)


# --- Действия меню -------------------------------------------------------------
@router.message(F.text == "📊 Структура БД")
async def db_sessions_info(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cols = con.execute("PRAGMA table_info(sessions);").fetchall()
        cnt = con.execute("SELECT COUNT(*) AS c FROM sessions;").fetchone()["c"]

        def safe_count_distinct(col: str):
            try:
                row = con.execute(f"SELECT COUNT(DISTINCT {col}) AS n FROM sessions;").fetchone()
                return row["n"]
            except Exception:
                return "—"

        has_stream = any(c["name"] == "stream_id" for c in cols)
        has_cohort = any(c["name"] == "cohort_id" for c in cols)
        ds = safe_count_distinct("stream_id")
        dc = safe_count_distinct("cohort_id")

    lines = [
        "📊 *sessions* — структура:",
        *(f"• {c['cid']}: {c['name']}  {c['type']}" for c in cols),
        "",
        f"Всего строк: *{cnt}*",
        f"Есть stream_id: *{has_stream}*  |  Есть cohort_id: *{has_cohort}*",
        f"Уникальных stream_id: *{ds}*  |  Уникальных cohort_id: *{dc}*",
        "",
        "Подсказка: при необходимости нажмите «🛠 Исправить sessions»",
    ]
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(F.text == "🛠 Исправить sessions")
async def db_fix_cohort(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cols = cur.execute("PRAGMA table_info(sessions);").fetchall()
        names = {c[1] for c in cols}  # c[1] = name

        # 1) добавить cohort_id, если нет
        if "cohort_id" not in names:
            cur.execute("ALTER TABLE sessions ADD COLUMN cohort_id INTEGER;")

        # 2) перенести данные из stream_id (если есть)
        if "stream_id" in names:
            cur.execute("""
                UPDATE sessions
                SET cohort_id = stream_id
                WHERE cohort_id IS NULL AND stream_id IS NOT NULL;
            """)

        # 3) индекс по новой колонке
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_cohort_start
            ON sessions(cohort_id, start_date);
        """)

        # 4) убрать старый индекс (если был)
        cur.execute("DROP INDEX IF EXISTS idx_sessions_stream_start;")

        con.commit()

    await message.answer("✅ Готово: cohort_id добавлен/обновлён, данные перенесены, индекс создан.")


@router.message(F.text == "📂 Индексы")
async def db_show_indexes(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("PRAGMA index_list(sessions);").fetchall()
    if not rows:
        await message.answer("Нет индексов в таблице sessions.")
    else:
        text = "📂 *Индексы sessions*:\n" + "\n".join(str(r) for r in rows)
        await message.answer(text, parse_mode="Markdown")
