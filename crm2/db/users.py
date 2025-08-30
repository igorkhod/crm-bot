# crm2/db/users.py
# Работа с таблицей users: выборки по cohort_id и по telegram_id.
# Самодостаточен: содержит собственный get_db_connection(), не зависит от crm2.db._impl.

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterable, Tuple

# Путь к базе: берём из env DB_PATH, иначе crm.db в корне проекта
DB_PATH = Path(os.getenv("DB_PATH", "crm.db")).resolve()


def get_db_connection() -> sqlite3.Connection:
    """
    Открывает подключение к SQLite с включёнными foreign_keys.
    Вызывающему важно закрыть соединение (используйте with ... as con).
    """
    con = sqlite3.connect(str(DB_PATH))
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Преобразует sqlite3.Row в словарь."""
    return {k: row[k] for k in row.keys()}


def _fetch_all(con: sqlite3.Connection, sql: str, args: Iterable[Any] = ()) -> List[sqlite3.Row]:
    con.row_factory = sqlite3.Row
    cur = con.execute(sql, tuple(args))
    try:
        return cur.fetchall()
    finally:
        cur.close()


def _fetch_one(con: sqlite3.Connection, sql: str, args: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    con.row_factory = sqlite3.Row
    cur = con.execute(sql, tuple(args))
    try:
        return cur.fetchone()
    finally:
        cur.close()


# ───────────────────────────────────────────────────────────────────────────────
# ПУБЛИЧНЫЕ ФУНКЦИИ
# ───────────────────────────────────────────────────────────────────────────────

def list_users_by_cohort(cohort_id: int) -> List[Dict[str, Any]]:
    """
    Вернёт список пользователей, привязанных к коорте (потоку).
    Поля: id, telegram_id, username, nickname, full_name, role, phone, email, cohort_id
    """
    sql = """
        SELECT
            id,
            telegram_id,
            username,
            nickname,
            full_name,
            role,
            phone,
            email,
            cohort_id
        FROM users
        WHERE cohort_id = ?
        ORDER BY COALESCE(full_name, username, nickname) COLLATE NOCASE
    """
    with get_db_connection() as con:
        rows = _fetch_all(con, sql, (cohort_id,))
    return [_row_to_dict(r) for r in rows]


def get_user_by_tg(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Вернёт данные пользователя по его telegram_id или None, если не найден.
    """
    sql = """
        SELECT
            id,
            telegram_id,
            username,
            nickname,
            full_name,
            role,
            phone,
            email,
            events,
            participants,
            cohort_id
        FROM users
        WHERE telegram_id = ?
        LIMIT 1
    """
    with get_db_connection() as con:
        row = _fetch_one(con, sql, (telegram_id,))
    return _row_to_dict(row) if row else None
