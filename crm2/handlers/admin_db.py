# crm2/handlers/admin_db.py
# Назначение: Административные команды для диагностики и исправления базы данных
# Функции:
# - db_sessions_info - Диагностика таблицы sessions (структура, статистика)
# - db_fix_cohort - Исправление структуры таблицы sessions (добавление cohort_id, миграция данных)
from __future__ import annotations

import sqlite3
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from crm2.db.sqlite import DB_PATH

# Центральный роутер этого модуля; подключается из app.py через безопасный include.

router = Router(name="admin_db")


@router.message(Command("db_sessions_info"))
async def db_sessions_info(message: Message):
    # УПРОЩЁННО: без проверки роли
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cols = con.execute("PRAGMA table_info(sessions);").fetchall()
        cnt = con.execute("SELECT COUNT(*) AS c FROM sessions;").fetchone()["c"]

        # аккуратно считаем разные поля — если столбца нет, не падаем
        def safe_count_distinct(col: str):
            try:
                row = con.execute(f"SELECT COUNT(DISTINCT {col}) AS n FROM sessions;").fetchone()
                return row["n"]
            except Exception:
                return "—"

        ds = safe_count_distinct("cohort_id")
        dc = safe_count_distinct("cohort_id")

    lines = [
        "🗄 *sessions* — структура:",
        *(f"• {c['cid']}: {c['name']}  {c['type']}" for c in cols),
        "",
        f"Всего строк: *{cnt}*",
        f"Есть cohort_id: *{any(c['name']=='cohort_id' for c in cols)}*  |  Есть cohort_id: *{any(c['name']=='cohort_id' for c in cols)}*",
        f"Уникальных cohort_id: *{ds}*  |  Уникальных cohort_id: *{dc}*",
        "",
        "Подсказка: при необходимости выполните /db_fix_cohort",
    ]
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("db_fix_cohort"))
async def db_fix_cohort(message: Message):
    # УПРОЩЁННО: без проверки роли
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cols = cur.execute("PRAGMA table_info(sessions);").fetchall()
        names = {c[1] for c in cols}  # c[1] = name

        # 1) добавить cohort_id, если нет
        if "cohort_id" not in names:
            cur.execute("ALTER TABLE sessions ADD COLUMN cohort_id INTEGER;")

        # 2) перенести данные из cohort_id (если есть)
        if "cohort_id" in names:
            cur.execute("""
                UPDATE sessions
                SET cohort_id = cohort_id
                WHERE cohort_id IS NULL AND cohort_id IS NOT NULL;
            """)

        # 3) индекс по новой колонке
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_cohort_start
            ON sessions(cohort_id, start_date);
        """)

        # 4) убрать старый индекс (если был)
        cur.execute("DROP INDEX IF EXISTS idx_sessions_cohort_start;")

        con.commit()

    await message.answer("✅ Готово: cohort_id добавлен/обновлён, данные перенесены, индекс создан.")