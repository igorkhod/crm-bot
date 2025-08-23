#
# === Файл: crm2/db/sqlite.py
# Аннотация: модуль CRM, доступ к SQLite/ORM. Внутри функции: get_db_connection, aget_db_connection, ensure_schema.
# Добавлено автоматически 2025-08-21 05:43:17

# crm2/db/sqlite.py
from __future__ import annotations

import sqlite3
import aiosqlite

from crm2.config import get_settings

# Единый путь к БД, берётся из ENV CRM_DB или дефолтный (на Render → /var/data/crm.db)
DB_PATH = get_settings().DB_PATH

def get_db_connection() -> sqlite3.Connection:
    """Синхронное подключение — для мест, где используется sqlite3 напрямую."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

async def aget_db_connection() -> aiosqlite.Connection:
    """Асинхронное подключение — для aiosqlite."""
    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("PRAGMA foreign_keys = ON")
    return conn

def ensure_schema() -> None:
    """Идемпотентно создаёт ключевые таблицы БД."""
    import sqlite3, os
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # users
        cur.execute("""
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
            participants TEXT,
            cohort_id    INTEGER
        )""")

        # cohorts
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cohorts (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT UNIQUE NOT NULL
        )""")

        # participants (связь user → cohort)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER UNIQUE,
            cohort_id  INTEGER,
            stream_id  INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        # streams (нужна логике входа)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS streams (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        )""")

        # consents (согласия на обработку)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS consents (
            telegram_id INTEGER PRIMARY KEY,
            given       INTEGER NOT NULL DEFAULT 0,
            ts          TEXT    DEFAULT CURRENT_TIMESTAMP
        )""")

        conn.commit()
