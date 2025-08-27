# crm2/db/users_repo.py
# Краткая аннотация: выборки пользователей для админ-панели (счётчик и страницы)

from typing import List, Tuple, Optional, Dict, Any
from sqlite3 import Row

from crm2.db.core import get_db_connection  # у тебя уже есть такой хелпер

def _row_to_dict(row: Row) -> Dict[str, Any]:
    if row is None:
        return {}
    return {
        "id": row["id"] if "id" in row.keys() else row[0],
        "telegram_id": row["telegram_id"] if "telegram_id" in row.keys() else None,
        "nickname": row["nickname"] if "nickname" in row.keys() else None,
        "full_name": row["full_name"] if "full_name" in row.keys() else None,
        "role": row["role"] if "role" in row.keys() else None,
        # поддержим обе схемы: stream_id и/или cohort_id
        "stream_id": row["stream_id"] if "stream_id" in row.keys() else None,
        "cohort_id": row["cohort_id"] if "cohort_id" in row.keys() else None,
    }

def _where_for_group(group_key: str) -> str:
    # Нормализуем поток: COALESCE(stream_id, cohort_id)
    if group_key == "stream_1":
        return "COALESCE(stream_id, cohort_id) = 1"
    if group_key == "stream_2":
        return "COALESCE(stream_id, cohort_id) = 2"
    if group_key == "new_intake":
        # Новый набор: нет потока и не админ
        return "COALESCE(stream_id, cohort_id) IS NULL AND (role IS NULL OR role NOT IN ('admin','alumni'))"
    if group_key == "alumni":
        # Окончившие: либо роль alumni, либо спец.флаг (если появится)
        return "role = 'alumni'"
    if group_key == "admins":
        return "role = 'admin'"
    return "1=1"

def count_users(group_key: str) -> int:
    where = _where_for_group(group_key)
    with get_db_connection() as con:
        cur = con.cursor()
        cur.execute(f"SELECT COUNT(*) FROM users WHERE {where}")
        n = cur.fetchone()[0]
    return int(n or 0)

def list_users(group_key: str, offset: int, limit: int) -> List[dict]:
    where = _where_for_group(group_key)
    with get_db_connection() as con:
        con.row_factory = Row  # чтобы обращаться по именам
        cur = con.cursor()
        cur.execute(
            f"""
            SELECT id, telegram_id, nickname, full_name, role,
                   COALESCE(stream_id, cohort_id) AS stream_id
            FROM users
            WHERE {where}
            ORDER BY COALESCE(full_name, nickname) COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]
