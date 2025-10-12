# crm2/db/sqlite.py
# Назначение: Единая точка подключения к SQLite (синхронное и асинхронное) с поддержкой режима только чтение
# Функции:
# - _query_only_enabled - Проверка, включен ли режим только чтения (через переменную окружения CRM_DB_QUERY_ONLY)
# - _apply_pragmas_sync - Применение PRAGMA для синхронного соединения
# - _apply_pragmas_async - Применение PRAGMA для асинхронного соединения
# - get_db_connection - Синхронное подключение к БД (с опциональным режимом только чтения)
# - aget_db_connection - Асинхронное подключение к БД (с опциональным режимом только чтения)
# - ensure_schema - Идемпотентное создание базовых таблиц users, cohorts, consents (в режиме записи)
from __future__ import annotations

import os
import sqlite3
import aiosqlite

from crm2.config import get_settings

# Единый путь к БД (на Render → /var/data/crm.db)
DB_PATH = get_settings().DB_PATH


def _query_only_enabled() -> bool:
    # По умолчанию включаем только чтение (безопасный режим бота)
    return os.getenv("CRM_DB_QUERY_ONLY", "1") == "1"


def _apply_pragmas_sync(conn: sqlite3.Connection, *, query_only: bool) -> None:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    # Разделяем режимы: читательский/пишущий
    conn.execute(f"PRAGMA query_only = {'ON' if query_only else 'OFF'};")
    # Небольшие улучшения стабильности
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")


async def _apply_pragmas_async(conn: aiosqlite.Connection, *, query_only: bool) -> None:
    conn.row_factory = sqlite3.Row  # aiosqlite понимает sqlite3.Row как row_factory
    await conn.execute("PRAGMA foreign_keys = ON;")
    await conn.execute(f"PRAGMA query_only = {'ON' if query_only else 'OFF'};")
    await conn.execute("PRAGMA journal_mode = WAL;")
    await conn.execute("PRAGMA synchronous = NORMAL;")


def get_db_connection(*, readonly: bool | None = None) -> sqlite3.Connection:
    """
    Синхронное подключение.
    readonly=None → берём режим из ENV CRM_DB_QUERY_ONLY (по умолчанию: только чтение).
    readonly=True/False → принудительно переопределяем.
    """
    if readonly is None:
        readonly = _query_only_enabled()
    conn = sqlite3.connect(DB_PATH)
    _apply_pragmas_sync(conn, query_only=readonly)
    return conn


async def aget_db_connection(*, readonly: bool | None = None) -> aiosqlite.Connection:
    """
    Асинхронное подключение (aiosqlite).
    readonly=None → берём режим из ENV CRM_DB_QUERY_ONLY (по умолчанию: только чтение).
    readonly=True/False → принудительно переопределяем.
    """
    if readonly is None:
        readonly = _query_only_enabled()
    conn = await aiosqlite.connect(DB_PATH)
    await _apply_pragmas_async(conn, query_only=readonly)
    return conn


def ensure_schema() -> None:
    """
    Идемпотентно создаёт базовые таблицы. ВАЖНО: всегда открываем соединение
    во ВКЛАДЫВАЕМОМ режиме записи (query_only=OFF), чтобы схема точно создалась
    даже если ENV по умолчанию — только чтение.
    """
    import os as _os
    if not _os.path.exists(DB_PATH):
        _os.makedirs(_os.path.dirname(DB_PATH), exist_ok=True)

    # Здесь принудительно пишущий режим
    with sqlite3.connect(DB_PATH) as conn:
        _apply_pragmas_sync(conn, query_only=False)
        cur = conn.cursor()

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
            cohort_id    INTEGER
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS cohorts (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT UNIQUE NOT NULL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS consents (
            telegram_id INTEGER PRIMARY KEY,
            given       INTEGER NOT NULL DEFAULT 0,
            ts          TEXT    DEFAULT CURRENT_TIMESTAMP
        )""")

        conn.commit()