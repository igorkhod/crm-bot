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

def get_upcoming_sessions(*, limit: int = 5, tg_id: int | None = None) -> List[Dict[str, Any]]:
    """
    Возвращает ближайшие занятия:
      - если передан tg_id, фильтруем по потоку пользователя;
      - иначе берём глобальное расписание (без потока).
    Всегда используем поля title/annotation как есть — НИКАКИХ «первых предложений».
    """
    con = get_db_connection()
    con.row_factory = sqlite3.Row

    rows: list[sqlite3.Row] = []
    if tg_id is not None:
        # 1) определяем stream_id пользователя (participants > users.cohort_id)
        sid_row = con.execute(
            """
            WITH usr AS (
              SELECT u.id AS uid, COALESCE(p.stream_id, u.cohort_id) AS sid
              FROM users u
              LEFT JOIN participants p ON p.user_id = u.id
              WHERE u.telegram_id = ?
              ORDER BY p.id DESC
              LIMIT 1
            )
            SELECT sid FROM usr
            """,
            (tg_id,),
        ).fetchone()
        stream_id = sid_row["sid"] if sid_row and sid_row["sid"] is not None else None

        if stream_id is not None:
            rows = con.execute(
                """
                SELECT
                    date        AS start_date,
                    date        AS end_date,
                    title       AS title,
                    NULL        AS topic_code,
                    COALESCE(annotation, '') AS annotation
                FROM events
                WHERE stream_id = ?
                  AND date(date) >= date('now')
                ORDER BY date
                LIMIT ?
                """,
                (stream_id, limit),
            ).fetchall()

    # fallback: без потока (например, если у юзера не назначен поток)
    if not rows:
        rows = con.execute(
            """
            SELECT
                date        AS start_date,
                date        AS end_date,
                title       AS title,
                NULL        AS topic_code,
                COALESCE(annotation, '') AS annotation
            FROM events
            WHERE date(date) >= date('now')
            ORDER BY date
            LIMIT ?
            """,
            (limit,),
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


# crm2/db/sessions.py
from __future__ import annotations
import sqlite3
from typing import Optional, List, Dict
from .core import get_db_connection

def get_user_stream(conn: sqlite3.Connection, tg_id: int) -> Optional[int]:
    """
    Возвращает stream_id пользователя:
    - сначала смотрим в participants (последняя запись)
    - если нет — берём users.cohort_id
    """
    row = conn.execute("""
        WITH usr AS (
          SELECT u.id   AS uid,
                 COALESCE(p.stream_id, u.cohort_id) AS sid,
                 p.id   AS pid
          FROM users u
          LEFT JOIN participants p ON p.user_id = u.id
          WHERE u.telegram_id = ?
          ORDER BY p.id DESC
          LIMIT 1
        )
        SELECT sid FROM usr
    """, (tg_id,)).fetchone()
    return row[0] if row and row[0] is not None else None


def get_upcoming_sessions(limit: int = 10, tg_id: Optional[int] = None) -> List[Dict]:
    """
    Возвращает ближайшие занятия из таблицы events.
    Если передан tg_id — фильтруем по потоку пользователя.
    """
    with get_db_connection() as con:
        stream_id = get_user_stream(con, tg_id) if tg_id else None
        if stream_id:
            rows = con.execute("""
                SELECT id,
                       date AS start_date,
                       date AS end_date,
                       title,
                       ''   AS annotation
                FROM events
                WHERE stream_id = ?
                  AND date(date) >= date('now')
                ORDER BY date
                LIMIT ?
            """, (stream_id, limit)).fetchall()
        else:
            rows = con.execute("""
                SELECT id,
                       date AS start_date,
                       date AS end_date,
                       title,
                       ''   AS annotation
                FROM events
                WHERE date(date) >= date('now')
                ORDER BY date
                LIMIT ?
            """, (limit,)).fetchall()

        return [dict(r) for r in rows]
