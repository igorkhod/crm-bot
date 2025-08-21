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
    """NO-OP в проде: никаких CREATE TABLE. Схемой управляем миграциями/ручками."""
    return