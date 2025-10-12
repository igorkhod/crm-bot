# crm2/db/bootstrap.py
# Назначение: Создание основных таблиц при запуске (users, cohorts) - идемпотентно
# Функции:
# - ensure_min_schema - Создает основные таблицы: users, cohorts (если их нет)

from __future__ import annotations
import sqlite3
from crm2.db.core import get_db_connection

def ensure_min_schema() -> None:
    """Ensure core tables exist on startup (idempotent)."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        # users
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER UNIQUE,
                username     TEXT,
                nickname     TEXT UNIQUE,
                password     TEXT,
                full_name    TEXT,
                role         TEXT DEFAULT 'user',
                phone        TEXT,
                email        TEXT,
                events       TEXT,
                cohort_id    INTEGER
            )
            """
        )
        # cohorts
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cohorts (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        # Таблица participants удалена - её функционал полностью покрывается таблицей attendance
        conn.commit()