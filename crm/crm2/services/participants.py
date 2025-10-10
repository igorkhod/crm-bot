# crm2/services/participants.py
from __future__ import annotations

import logging
from typing import Iterable, List, Optional, Tuple

from crm2.db.core import get_db_connection


def get_streams() -> List[Tuple[int, str]]:
    """
    Возвращает список потоков (id, title).
    Если таблица пуста — вернётся пустой список.
    """
    with get_db_connection() as con:
        cur = con.execute("SELECT id, title FROM streams ORDER BY id")
        rows = cur.fetchall()
    return [(r[0], r[1]) for r in rows]


def upsert_participant_stream(user_id: int, stream_id: int) -> None:
    """
    Назначает пользователю поток (INSERT ... ON CONFLICT UPDATE).
    Таблица participants имеет UNIQUE(user_id).
    """
    sql = """
    INSERT INTO participants (user_id, stream_id)
    VALUES (?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
      stream_id = excluded.stream_id
    """
    with get_db_connection() as con:
        con.execute(sql, (user_id, stream_id))
        con.commit()


def users_missing_stream(limit: int = 50) -> List[dict]:
    """
    Пользователи, у кого нет строки в participants ИЛИ stream_id NULL.
    Берём только реальных пользователей (где есть хоть какой-то tg/ФИО).
    """
    sql = """
    SELECT u.id, u.telegram_id, u.username, u.full_name, u.cohort_id,
           p.stream_id
    FROM users u
    LEFT JOIN participants p ON p.user_id = u.id
    WHERE (p.user_id IS NULL OR p.stream_id IS NULL)
      AND (u.telegram_id IS NOT NULL OR u.full_name IS NOT NULL)
    ORDER BY u.id
    LIMIT ?
    """
    with get_db_connection() as con:
        cur = con.execute(sql, (limit,))
        rows = cur.fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "user_id": r[0],
                "telegram_id": r[1],
                "username": r[2] or "",
                "full_name": r[3] or "",
                "cohort_id": r[4],
                "stream_id": r[5],  # None
            }
        )
    return out


def get_user_id_by_tg(telegram_id: int) -> Optional[int]:
    with get_db_connection() as con:
        cur = con.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
    return row[0] if row else None
