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

def _cohort_expr(cols: set) -> str:
    """
    Возвращает корректное SQL-выражение для 'потока':
    - если есть cohort_id → cohort_id
    - иначе если есть cohort_id → cohort_id
    - иначе → NULL
    """
    if "cohort_id" in cols:
        return "cohort_id"
    if "cohort_id" in cols:
        return "cohort_id"
    return "NULL"

def _where_for_group(group_key: str, cols: set) -> str:
    s = _cohort_expr(cols)
    if group_key == "cohort_1":
        return f"{s} = 1"
    if group_key == "cohort_2":
        return f"{s} = 2"
    if group_key == "new_intake":
        # нет потока и не админ/не alumni
        return f"{s} IS NULL AND (role IS NULL OR role NOT IN ('admin','alumni'))"
    if group_key == "alumni":
        return "role = 'alumni'"
    if group_key == "admins":
        return "role = 'admin'"
    return "1=1"

from sqlite3 import Row

def _row_to_dict(row: Row) -> dict:
    k = set(row.keys())  # имена доступных колонок в Row
    return {
        "id": row["id"] if "id" in k else None,
        "telegram_id": row["telegram_id"] if "telegram_id" in k else None,
        "nickname": row["nickname"] if "nickname" in k else None,
        "full_name": row["full_name"] if "full_name" in k else None,
        "role": row["role"] if "role" in k else None,
        # В SELECT мы возвращаем псевдоколонку AS cohort_id — читаем её, если есть
        "cohort_id": row["cohort_id"] if "cohort_id" in k else None,
        # На всякий случай — если когда-то вернём cohort_id в SELECT
        "cohort_id": row["cohort_id"] if "cohort_id" in k else None,
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
        s = _cohort_expr(cols)  # корректное выражение для SELECT

        cur = con.execute(
            f"""
            SELECT id, telegram_id, nickname, full_name, role,
                   {s} AS cohort_id
            FROM users
            WHERE {where}
            ORDER BY COALESCE(full_name, nickname) COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]
