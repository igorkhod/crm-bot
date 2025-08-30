# crm2/handlers/admin_db_doctor.py
from __future__ import annotations

import sqlite3
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from crm2.db.sqlite import DB_PATH

router = Router(name="admin_db_doctor")


# ---------- утилиты ------------------------------------------------------------
def _txt(s: str) -> str:
    """Нормализуем текст кнопки/сообщения (убираем лишние пробелы, приводим к нижнему регистру)."""
    return " ".join((s or "").strip().split()).lower()

BTN_MENU     = "🩺 db doctor"
BTN_STRUCT   = "📊 структура бд"
BTN_FIX      = "🛠 исправить sessions"
BTN_INDEXES  = "📂 индексы"
BTN_BACK     = "↩️ главное меню"


# ---------- меню ---------------------------------------------------------------
async def show_menu(message: Message) -> None:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Структура БД"), KeyboardButton(text="🛠 Исправить sessions")],
            [KeyboardButton(text="📂 Индексы"),      KeyboardButton(text="↩️ Главное меню")],
        ],
        resize_keyboard=True,
    )
    await message.answer("🩺 DB Doctor — выбор действия:", reply_markup=kb)


@router.message(F.text.func(lambda t: _txt(t) == BTN_MENU))
async def db_doctor_menu(message: Message):
    await show_menu(message)


# ---------- команды-дублёры ---------------------------------------------------
@router.message(Command("db_sessions_info"))
async def cmd_sessions_info(message: Message):
    await action_sessions_info(message)

@router.message(Command("db_fix_cohort"))
async def cmd_fix_cohort(message: Message):
    await action_fix_sessions(message)

@router.message(Command("db_indexes"))
async def cmd_indexes(message: Message):
    await action_indexes(message)


# ---------- действия (по кнопкам/тексту) --------------------------------------
@router.message(F.text.func(lambda t: _txt(t) == BTN_STRUCT) | F.text.func(lambda t: _txt(t) == "структура бд"))
async def action_sessions_info(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cols = con.execute("PRAGMA table_info(sessions);").fetchall()
        cnt  = con.execute("SELECT COUNT(*) AS c FROM sessions;").fetchone()["c"]

        def safe_count(col: str):
            try:
                return con.execute(f"SELECT COUNT(DISTINCT {col}) AS n FROM sessions;").fetchone()["n"]
            except Exception:
                return "—"

        has_stream = any(c["name"] == "stream_id" for c in cols)
        has_cohort = any(c["name"] == "cohort_id" for c in cols)

    lines = [
        "📊 *sessions* — структура:",
        *(f"• {c['cid']}: {c['name']}  {c['type']}" for c in cols),
        "",
        f"Всего строк: *{cnt}*",
        f"Есть stream_id: *{has_stream}*  |  Есть cohort_id: *{has_cohort}*",
        f"Уникальных stream_id: *{safe_count('stream_id')}*  |  Уникальных cohort_id: *{safe_count('cohort_id')}*",
        "",
        "Подсказка: при необходимости нажмите «🛠 Исправить sessions».",
    ]
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(F.text.func(lambda t: _txt(t) == BTN_FIX) | F.text.func(lambda t: _txt(t) == "исправить sessions"))
async def action_fix_sessions(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        names = {c[1] for c in cur.execute("PRAGMA table_info(sessions);").fetchall()}

        if "cohort_id" not in names:
            cur.execute("ALTER TABLE sessions ADD COLUMN cohort_id INTEGER;")

        if "stream_id" in names:
            cur.execute("""
                UPDATE sessions
                SET cohort_id = stream_id
                WHERE cohort_id IS NULL AND stream_id IS NOT NULL;
            """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_cohort_start
            ON sessions(cohort_id, start_date);
        """)
        cur.execute("DROP INDEX IF EXISTS idx_sessions_stream_start;")
        con.commit()

    await message.answer("✅ Готово: cohort_id добавлен/обновлён, данные перенесены, индекс создан.")


@router.message(F.text.func(lambda t: _txt(t) == BTN_INDEXES) | F.text.func(lambda t: _txt(t) == "индексы"))
async def action_indexes(message: Message):
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute("PRAGMA index_list(sessions);").fetchall()
    if not rows:
        await message.answer("Нет индексов в таблице sessions.")
    else:
        text = "📂 *Индексы sessions*:\n" + "\n".join(str(r) for r in rows)
        await message.answer(text, parse_mode="Markdown")


@router.message(F.text.func(lambda t: _txt(t) == BTN_BACK) | F.text.func(lambda t: _txt(t) == "главное меню"))
async def action_back_to_main(message: Message):
    # переиспользуем уже готовый рендер главного меню
    from crm2.handlers import info as info_router
    # в info.py (или соответствующем модуле) должен быть хэндлер back_to_main(message)
    try:
        await info_router.back_to_main(message)
    except Exception:
        await message.answer("Главное меню:", reply_markup=None)
