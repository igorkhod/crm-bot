# crm2/db/users.py
from __future__ import annotations
import sqlite3
from typing import List, Tuple
from .core import get_db_connection

def list_users_by_cohort_id(cohort_id: int) -> List[Tuple[int, str]]:
    """
    Возвращает [(user_id, display_name)] для указанного потока.
    Ожидается, что в таблице users есть поле cohort_id (INTEGER).
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT id, COALESCE(full_name, nickname, '') AS name "
            "FROM users WHERE cohort_id=? ORDER BY name COLLATE NOCASE",
            (cohort_id,)
        ).fetchall()
        return [(r["id"], r["name"] or f"#{r['id']}") for r in rows]
