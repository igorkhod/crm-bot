# crm2/db/users_repo.py
from typing import List, Dict, Any
from sqlite3 import Row
import sqlite3

from crm2.db.core import get_db_connection

# ---- вспомогательные ---------------------------------------------------------

def _users_columns(con: sqlite3.Connection) -> set:
    # набор колонок таблицы users
    rows = con.execute("PRAGMA table_info(users)").fetchall()
    return {r[1] for r in rows}  # r[1] = name

def _stream_expr(cols: set) -> str:
    """
    Возвращает корректное SQL-выражение для 'потока':
    - если есть stream_id → stream_id
    - иначе если есть cohort_id → cohort_id
    - иначе → NULL
    """
    if "stream_id" in cols:
        return "stream_id"
    if "cohort_id" in cols:
        return "cohort_id"
    return "NULL"

def _where_for_group(group_key: str, cols: set) -> str:
    s = _stream_expr(cols)
    if group_key == "stream_1":
        return f"{s} = 1"
    if group_key == "stream_2":
        return f"{s} = 2"
    if group_key == "new_intake":
        # нет потока и не админ/не alumni
        return f"{s} IS NULL AND (role IS NULL OR role NOT IN ('admin','alumni'))"
    if group_key == "alumni":
        return "role = 'alumni'"
    if group_key == "admins":
        return "role = 'admin'"
    return "1=1"

def _row_to_dict(row: Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "telegram_id": row.get("telegram_id"),
        "nickname": row.get("nickname"),
        "full_name": row.get("full_name"),
        "role": row.get("role"),
        # В SELECT мы будем возвращать псевдоколонку AS stream_id
        "stream_id": row.get("stream_id"),
    }

# ---- публичные функции -------------------------------------------------------

def count_users(group_key: str) -> int:
    with get_db_connection() as con:
        cols = _users_columns(con)
        where = _where_for_group(group_key, cols)
        cur = con.execute(f"SELECT COUNT(*) FROM users WHERE {where}")
        return int(cur.fetchone()[0] or 0)

def list_users(group_key: str, offset: int, limit: int) -> List[dict]:
    with get_db_connection() as con:
        con.row_factory = Row
        cols = _users_columns(con)
        where = _where_for_group(group_key, cols)
        s = _stream_expr(cols)  # корректное выражение для SELECT

        cur = con.execute(
            f"""
            SELECT id, telegram_id, nickname, full_name, role,
                   {s} AS stream_id
            FROM users
            WHERE {where}
            ORDER BY COALESCE(full_name, nickname) COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]
