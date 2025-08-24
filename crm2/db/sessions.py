
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from .core import get_db_connection


# ---------- helpers ----------

def _row2dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,)
    )
    return cur.fetchone() is not None


def _cols(con: sqlite3.Connection, table: str) -> List[str]:
    return [r["name"] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]


def _pick(existing: List[str], candidates: List[str]) -> Optional[str]:
    """Pick the first column from candidates that exists in `existing`."""
    s = set(existing)
    for c in candidates:
        if c in s:
            return c
    return None


# ---------- user/stream helpers ----------

def get_user_stream_title_by_tg(tg_id: int) -> Tuple[Optional[int], Optional[str]]:
    """
    Return (stream_id, stream_title) resolved by user's telegram_id.
    Looks into participants.stream_id first; falls back to users.cohort_id.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row

        # user id
        u = con.execute(
            "SELECT id, COALESCE(full_name, username, nickname) AS full_name, role, cohort_id "
            "FROM users WHERE telegram_id=? LIMIT 1",
            (tg_id,),
        ).fetchone()
        if not u:
            return None, None
        uid = u["id"]

        # participants priority
        p = con.execute(
            "SELECT stream_id FROM participants WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (uid,),
        ).fetchone()

        stream_id = p["stream_id"] if (p and p["stream_id"]) is not None else u["cohort_id"]

        if stream_id is None:
            return None, None

        # streams title
        st = con.execute(
            "SELECT title FROM streams WHERE id=? LIMIT 1", (stream_id,)
        ).fetchone()
        return int(stream_id), (st["title"] if st else None)


def _get_user_stream_id(con: sqlite3.Connection, tg_id: int) -> Optional[int]:
    row = con.execute(
        """
        WITH u AS (
            SELECT id, cohort_id
            FROM users
            WHERE telegram_id=?
            LIMIT 1
        ),
        p AS (
            SELECT stream_id
            FROM participants
            WHERE user_id=(SELECT id FROM u LIMIT 1)
            ORDER BY id DESC
            LIMIT 1
        )
        SELECT COALESCE(p.stream_id, u.cohort_id) AS stream_id
        FROM u LEFT JOIN p ON 1=1
        """,
        (tg_id,),
    ).fetchone()
    return int(row["stream_id"]) if (row and row["stream_id"] is not None) else None


# ---------- session readers ----------

def _select_from_sessions(con: sqlite3.Connection, *, stream_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    cols = _cols(con, "sessions")
    id_col = "id"
    start_col = _pick(cols, ["start_date", "start", "date"])
    end_col = _pick(cols, ["end_date", "end", "date"])
    topic_col = _pick(cols, ["topic_code", "code", "topic"])
    title_col = _pick(cols, ["title", "name"])
    ann_col = _pick(cols, ["annotation", "ann", "description", "desc"])
    stream_col = _pick(cols, ["stream_id", "cohort_id"])

    if start_col is None:
        raise RuntimeError("Table 'sessions' has no start_date/start/date column")

    # Build WHERE
    where = f"date({start_col}) >= date('now')"
    params: List[Any] = []
    if stream_id is not None and stream_col is not None:
        where += f" AND {stream_col}=?"
        params.append(stream_id)

    # Build SELECT columns with aliases
    select_cols = [f"{id_col} AS id", f"{start_col} AS start_date"]
    select_cols.append(f"{end_col} AS end_date" if end_col else f"{start_col} AS end_date")
    select_cols.append(f"{topic_col} AS topic_code" if topic_col else "NULL AS topic_code")
    select_cols.append(f"{title_col} AS title" if title_col else "NULL AS title")
    select_cols.append(f"{ann_col} AS annotation" if ann_col else "'' AS annotation")

    sql = f"""
        SELECT {', '.join(select_cols)}
        FROM sessions
        WHERE {where}
        ORDER BY {start_col}
        LIMIT ?
    """
    params.append(limit)
    rows = con.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _select_from_events(con: sqlite3.Connection, *, stream_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    # Fallback: events(date,title,?stream_id)
    cols = _cols(con, "events")
    id_col = "id"
    date_col = _pick(cols, ["date", "event_date", "start", "start_date"]) or "date"
    title_col = _pick(cols, ["title", "name"])
    ann_col = _pick(cols, ["annotation", "ann", "description", "desc"])
    stream_col = _pick(cols, ["stream_id", "cohort_id"])

    where = f"date({date_col}) >= date('now')"
    params: List[Any] = []
    if stream_id is not None and stream_col is not None:
        where += f" AND {stream_col}=?"
        params.append(stream_id)

    select_cols = [f"{id_col} AS id",
                   f"{date_col} AS start_date",
                   f"{date_col} AS end_date"]
    select_cols.append(f"{title_col} AS title" if title_col else "NULL AS title")
    select_cols.append(f"{ann_col} AS annotation" if ann_col else "'' AS annotation")
    select_cols.append("NULL AS topic_code")

    sql = f"""
        SELECT {', '.join(select_cols)}
        FROM events
        WHERE {where}
        ORDER BY {date_col}
        LIMIT ?
    """
    params.append(limit)
    rows = con.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_upcoming_sessions(*, limit: int = 5, tg_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Returns list of upcoming sessions for the user's stream (if resolvable).
    Produces a unified row format:
      {id, start_date, end_date, topic_code, title, annotation}
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        stream_id = _get_user_stream_id(con, tg_id) if tg_id is not None else None

        if _table_exists(con, "sessions"):
            return _select_from_sessions(con, stream_id=stream_id, limit=limit)

        if _table_exists(con, "events"):
            return _select_from_events(con, stream_id=stream_id, limit=limit)

        # Nothing to read from:
        return []


def get_session_by_id(session_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row

        if _table_exists(con, "sessions"):
            cols = _cols(con, "sessions")
            id_col = "id"
            start_col = _pick(cols, ["start_date", "start", "date"])
            end_col = _pick(cols, ["end_date", "end", "date"])
            topic_col = _pick(cols, ["topic_code", "code", "topic"])
            title_col = _pick(cols, ["title", "name"])
            ann_col = _pick(cols, ["annotation", "ann", "description", "desc"])

            select_cols = [f"{id_col} AS id",
                           f"{start_col} AS start_date" if start_col else "NULL AS start_date",
                           f"{end_col} AS end_date" if end_col else (f"{start_col} AS end_date" if start_col else "NULL AS end_date"),
                           f"{topic_col} AS topic_code" if topic_col else "NULL AS topic_code",
                           f"{title_col} AS title" if title_col else "NULL AS title",
                           f"{ann_col} AS annotation" if ann_col else "'' AS annotation"]
            sql = f"SELECT {', '.join(select_cols)} FROM sessions WHERE {id_col}=? LIMIT 1"
            row = con.execute(sql, (session_id,)).fetchone()
            return dict(row) if row else None

        if _table_exists(con, "events"):
            cols = _cols(con, "events")
            id_col = "id"
            date_col = _pick(cols, ["date", "event_date", "start", "start_date"]) or "date"
            title_col = _pick(cols, ["title", "name"])
            ann_col = _pick(cols, ["annotation", "ann", "description", "desc"])

            select_cols = [f"{id_col} AS id",
                           f"{date_col} AS start_date",
                           f"{date_col} AS end_date",
                           f"{title_col} AS title" if title_col else "NULL AS title",
                           f"{ann_col} AS annotation" if ann_col else "'' AS annotation",
                           "NULL AS topic_code"]
            sql = f"SELECT {', '.join(select_cols)} FROM events WHERE {id_col}=? LIMIT 1"
            row = con.execute(sql, (session_id,)).fetchone()
            return dict(row) if row else None

    return None
