# crm2/db/users.py
from __future__ import annotations

import sqlite3
from typing import List, Tuple
from .core import get_db_connection

def list_users_by_cohort(cohort_id: int) -> List[Tuple[int, str]]:
    """
    Возвращает список пользователей коорты (потока):
    [(user_id, display_name)], где display_name = full_name / nickname / username.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """
            SELECT id,
                   COALESCE(NULLIF(TRIM(full_name), ''),
                            NULLIF(TRIM(nickname), ''),
                            NULLIF(TRIM(username), ''),
                            '#' || id) AS name
            FROM users
            WHERE cohort_id = ?
            ORDER BY name COLLATE NOCASE
            """,
            (cohort_id,),
        ).fetchall()
        return [(r["id"], r["name"]) for r in rows]

# На всякий случай сохраняем обратную совместимость:
def list_users_by_stream(stream_id: int):
    return list_users_by_cohort(stream_id)
