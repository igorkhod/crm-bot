# === Автогенерированный заголовок: crm2/db/attendance.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: get_last_attendance, get_summary, _table_exists
# === Конец автозаголовка
# crm2/db/attendance.py
from __future__ import annotations
import sqlite3
from typing import Tuple, List
from .core import get_db_connection
from crm2.db.sessions import get_upcoming_sessions_by_cohort, get_recent_past_sessions_by_cohort
from crm2.db.users import list_users_by_cohort

def get_last_attendance(user_id: int, limit: int = 3) -> List[tuple]:
    """
    Возвращает последние limit записей по посещаемости пользователя:
    (session_id, status, noted_at)
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        if not _table_exists(con, "attendance"):
            return []
        rows = con.execute(
            "SELECT session_id, status, noted_at FROM attendance "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [ (r["session_id"], r["status"], r["noted_at"]) for r in rows ]

def get_summary(user_id: int) -> Tuple[int,int,int]:
    """
    Возвращает кортеж: (present, absent, late) всего по пользователю.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        if not _table_exists(con, "attendance"):
            return (0,0,0)
        sums = {"present":0,"absent":0,"late":0}
        for st in sums.keys():
            r = con.execute(
                "SELECT COUNT(*) AS cnt FROM attendance WHERE user_id=? AND status=?",
                (user_id, st)
            ).fetchone()
            sums[st] = r["cnt"] if r else 0
        return (sums["present"], sums["absent"], sums["late"])

def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,)
    )
    return cur.fetchone() is not None
