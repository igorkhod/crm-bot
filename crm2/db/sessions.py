from __future__ import annotations
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from .core import get_db_connection


def _row2dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def get_user_stream_title_by_tg(tg_id: int) -> Tuple[Optional[int], Optional[str]]:
    """
    Вернёт (stream_id, stream_title) для пользователя по его telegram_id.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            """
            SELECT p.stream_id AS sid, s.title AS stitle
            FROM users u
            JOIN participants p ON p.user_id = u.id
            JOIN streams s      ON s.id = p.stream_id
            WHERE u.telegram_id = ?
            ORDER BY p.id ASC
            LIMIT 1
            """,
            (tg_id,),
        ).fetchone()
        if not row:
            return None, None
        return row["sid"], row["stitle"]


def get_upcoming_sessions(*, limit: int = 5, tg_id: Optional[int] = None,
                          stream_id: Optional[int] = None) -> List[Dict]:
    """
    Список ближайших занятий: только для нужного потока.
    Если stream_id не задан, берём его по tg_id.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row

        sid = stream_id
        if sid is None and tg_id is not None:
            sid, _ = get_user_stream_title_by_tg(tg_id)

        if sid is None:
            # Поток не определён — вернём пусто
            return []

        rows = con.execute(
            """
            SELECT id, date, stream_id, title
            FROM events
            WHERE stream_id = ?
              AND date(date) >= date('now')
            ORDER BY date(date)
            LIMIT ?
            """,
            (sid, limit),
        ).fetchall()
        return [dict(r) for r in rows]



def get_session_by_id(session_id: int) -> Optional[Dict]:
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT id, date, stream_id, title FROM events WHERE id = ?",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None

