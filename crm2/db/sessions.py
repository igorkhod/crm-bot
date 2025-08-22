from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from .core import get_db_connection


def _row2dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def get_user_stream_title_by_tg(tg_id: int) -> Tuple[Optional[int], Optional[str]]:
    """
    Возвращает (stream_id, stream_title) по telegram_id пользователя.
    Сначала берём из participants→streams, при отсутствии — пытаемся
    сопоставить users.cohort_id со streams.id.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row

        cur = con.execute(
            """
            SELECT p.stream_id, s.title AS stream_title
            FROM users u
            LEFT JOIN participants p ON p.user_id = u.id
            LEFT JOIN streams s      ON s.id = p.stream_id
            WHERE u.telegram_id = ?
            ORDER BY p.id ASC
            LIMIT 1
            """,
            (tg_id,),
        )
        row = cur.fetchone()
        if row and row["stream_id"]:
            return row["stream_id"], row["stream_title"]

        # fallback: users.cohort_id → streams.id
        cur = con.execute(
            "SELECT cohort_id FROM users WHERE telegram_id = ?",
            (tg_id,),
        )
        row = cur.fetchone()
        if row and row["cohort_id"]:
            cur2 = con.execute(
                "SELECT id, title FROM streams WHERE id = ?",
                (row["cohort_id"],),
            )
            r2 = cur2.fetchone()
            if r2:
                return r2["id"], r2["title"]

        return None, None


def get_upcoming_sessions(
    limit: int = 5, tg_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Выдаёт ближайшие занятия из таблицы events.
    Если передан tg_id — фильтруем по потоку пользователя.
    Возвращаем список словарей с ключами:
      id, start_date, end_date, title, annotation
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row

        params: List[Any] = []
        where = ["date(date) >= date('now')"]

        if tg_id is not None:
            stream_id, _ = get_user_stream_title_by_tg(tg_id)
            if stream_id:
                where.append("stream_id = ?")
                params.append(stream_id)

        sql = f"""
            SELECT
                id,
                date           AS start_date,
                date           AS end_date,
                title,
                NULL           AS annotation
            FROM events
            WHERE {' AND '.join(where)}
            ORDER BY date
            LIMIT ?
        """
        params.append(limit)

        cur = con.execute(sql, params)
        return [_row2dict(r) for r in cur.fetchall()]


def get_session_by_id(session_id: int) -> Optional[Dict[str, Any]]:
    """
    Полная карточка занятия по id (для клика по кнопке).
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            """
            SELECT
                id,
                date  AS start_date,
                date  AS end_date,
                title,
                NULL  AS annotation
            FROM events
            WHERE id = ?
            """,
            (session_id,),
        )
        row = cur.fetchone()
        return _row2dict(row) if row else None
