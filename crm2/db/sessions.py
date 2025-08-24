
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .core import get_db_connection


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
    s = set(existing)
    for c in candidates:
        if c in s:
            return c
    return None


# ---------- user/stream helpers ----------

def get_user_stream_title_by_tg(tg_id: int) -> Tuple[Optional[int], Optional[str]]:
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row

        u = con.execute(
            "SELECT id, COALESCE(full_name, username, nickname) AS full_name, role, cohort_id "
            "FROM users WHERE telegram_id=? LIMIT 1",
            (tg_id,),
        ).fetchone()
        if not u:
            return None, None
        uid = u["id"]

        p = con.execute(
            "SELECT stream_id FROM participants WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (uid,),
        ).fetchone()

        stream_id = p["stream_id"] if (p and p["stream_id"]) is not None else u["cohort_id"]
        if stream_id is None:
            return None, None

        # streams/cohorts title
        title = None
        if _table_exists(con, "streams"):
            r = con.execute("SELECT title FROM streams WHERE id=? LIMIT 1", (stream_id,)).fetchone()
            title = r["title"] if r else None
        if title is None and _table_exists(con, "cohorts"):
            r = con.execute("SELECT title FROM cohorts WHERE id=? LIMIT 1", (stream_id,)).fetchone()
            title = r["title"] if r else None

        return int(stream_id), title


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


# ---------- sessions readers ----------

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

    where = f"date({start_col}) >= date('now')"
    params: List[Any] = []
    if stream_id is not None and stream_col is not None:
        where += f" AND {stream_col}=?"
        params.append(stream_id)

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


def _select_from_session_days(con: sqlite3.Connection, *, stream_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    """
    Build sessions from per-day records in session_days table.
    Adjacent days (diff=1) with same stream and same topic_code/topic_id are grouped.
    Result id is the id of the first day in the group.
    """
    cols = _cols(con, "session_days")
    id_col = "id"
    day_col = _pick(cols, ["day", "date", "day_date", "session_day"]) or "date"
    stream_col = _pick(cols, ["stream_id", "cohort_id"])
    topic_code_col = _pick(cols, ["topic_code", "code"])
    topic_id_col = _pick(cols, ["topic_id"])

    # Build base SQL
    where = f"date({day_col}) >= date('now')"
    params: List[Any] = []
    if stream_id is not None and stream_col is not None:
        where += f" AND {stream_col}=?"
        params.append(stream_id)

    select_cols = [f"{id_col} AS id", f"{day_col} AS day"]
    if topic_code_col:
        select_cols.append(f"{topic_code_col} AS topic_code")
        join_topics = False
    elif topic_id_col and _table_exists(con, "topics"):
        select_cols.append(f"{topic_id_col} AS topic_id")
        join_topics = True
    else:
        select_cols.append("NULL AS topic_code")
        join_topics = False

    if stream_col:
        select_cols.append(f"{stream_col} AS stream_id")
    else:
        select_cols.append("NULL AS stream_id")

    sql = f"SELECT {', '.join(select_cols)} FROM session_days WHERE {where} ORDER BY {day_col}"
    rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    if not rows:
        return []

    # If we need topics join, fetch all topic fields:
    topics_by_id: Dict[int, Dict[str, str]] = {}
    if join_topics:
        for tr in con.execute("SELECT id, code AS topic_code, title, annotation FROM topics").fetchall():
            topics_by_id[int(tr["id"])] = {
                "topic_code": tr["topic_code"],
                "title": tr["title"],
                "annotation": tr["annotation"] or "",
            }

    # Sort by day (ensure) and group
    def parse_d(s: str) -> datetime:
        return datetime.fromisoformat(s) if "T" in s else datetime.strptime(s, "%Y-%m-%d")

    items = []
    for r in rows:
        d = parse_d(r["day"]).date()
        code = r.get("topic_code")
        title = ""
        ann = ""
        if not code and join_topics:
            tinfo = topics_by_id.get(int(r.get("topic_id") or 0))
            if tinfo:
                code = tinfo.get("topic_code")
                title = tinfo.get("title") or ""
                ann = tinfo.get("annotation") or ""
        items.append({
            "id": int(r["id"]),
            "day": d,
            "stream_id": r.get("stream_id"),
            "topic_code": code,
            "title": title,
            "annotation": ann,
        })

    items.sort(key=lambda x: x["day"])

    groups: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None

    for it in items:
        if cur is None:
            cur = {
                "id": it["id"],
                "start_date": it["day"].isoformat(),
                "end_date": it["day"].isoformat(),
                "topic_code": it["topic_code"],
                "title": it["title"],
                "annotation": it["annotation"],
                "stream_id": it["stream_id"],
            }
            continue

        prev_end = datetime.fromisoformat(cur["end_date"]).date()
        cond_adjacent = (it["day"] - prev_end) == timedelta(days=1)
        same_stream = (cur["stream_id"] == it["stream_id"]) or (cur["stream_id"] is None or it["stream_id"] is None)
        same_topic = (cur["topic_code"] == it["topic_code"]) or (not cur["topic_code"] or not it["topic_code"])

        if cond_adjacent and same_stream and same_topic:
            # extend
            cur["end_date"] = it["day"].isoformat()
            if not cur["topic_code"]:
                cur["topic_code"] = it["topic_code"]
            if not cur["title"]:
                cur["title"] = it["title"]
            if not cur["annotation"]:
                cur["annotation"] = it["annotation"]
        else:
            groups.append(cur)
            cur = {
                "id": it["id"],
                "start_date": it["day"].isoformat(),
                "end_date": it["day"].isoformat(),
                "topic_code": it["topic_code"],
                "title": it["title"],
                "annotation": it["annotation"],
                "stream_id": it["stream_id"],
            }

    if cur is not None:
        groups.append(cur)

    # Trim to limit
    groups = groups[:limit]

    # Normalize keys
    for g in groups:
        for k in list(g.keys()):
            if k not in ("id", "start_date", "end_date", "topic_code", "title", "annotation"):
                g.pop(k, None)

    return groups


def get_upcoming_sessions(*, limit: int = 5, tg_id: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        stream_id = _get_user_stream_id(con, tg_id) if tg_id is not None else None

        if _table_exists(con, "sessions"):
            return _select_from_sessions(con, stream_id=stream_id, limit=limit)
        if _table_exists(con, "events"):
            return _select_from_events(con, stream_id=stream_id, limit=limit)
        if _table_exists(con, "session_days"):
            return _select_from_session_days(con, stream_id=stream_id, limit=limit)

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

            sql = f"SELECT {id_col} AS id, {start_col} AS start_date, {end_col or start_col} AS end_date, " \
                  f"{(topic_col + ' AS topic_code') if topic_col else 'NULL AS topic_code'}, " \
                  f"{(title_col + ' AS title') if title_col else 'NULL AS title'}, " \
                  f"{(ann_col + ' AS annotation') if ann_col else "'' AS annotation"} " \
                  f"FROM sessions WHERE {id_col}=? LIMIT 1"
            row = con.execute(sql, (session_id,)).fetchone()
            if row:
                return dict(row)

        if _table_exists(con, "events"):
            cols = _cols(con, "events")
            id_col = "id"
            date_col = _pick(cols, ["date", "event_date", "start", "start_date"]) or "date"
            title_col = _pick(cols, ["title", "name"])
            ann_col = _pick(cols, ["annotation", "ann", "description", "desc"])

            sql = f"SELECT {id_col} AS id, {date_col} AS start_date, {date_col} AS end_date, " \
                  f"{(title_col + ' AS title') if title_col else 'NULL AS title'}, " \
                  f"{(ann_col + ' AS annotation') if ann_col else "'' AS annotation"}, " \
                  f"NULL AS topic_code FROM events WHERE {id_col}=? LIMIT 1"
            row = con.execute(sql, (session_id,)).fetchone()
            if row:
                return dict(row)

        # Interpret as first-day id in session_days group
        if _table_exists(con, "session_days"):
            cols = _cols(con, "session_days")
            id_col = "id"
            day_col = _pick(cols, ["day", "date", "day_date", "session_day"]) or "date"
            stream_col = _pick(cols, ["stream_id", "cohort_id"])
            topic_code_col = _pick(cols, ["topic_code", "code"])
            topic_id_col = _pick(cols, ["topic_id"])

            base = con.execute(
                f"SELECT {id_col} AS id, {day_col} AS day, "
                f"{(topic_code_col + ' AS topic_code') if topic_code_col else 'NULL AS topic_code'}, "
                f"{(topic_id_col + ' AS topic_id') if topic_id_col else 'NULL AS topic_id'}, "
                f"{(stream_col + ' AS stream_id') if stream_col else 'NULL AS stream_id'} "
                f"FROM session_days WHERE {id_col}=? LIMIT 1",
                (session_id,),
            ).fetchone()
            if not base:
                return None

            # expand to adjacent +/- 1 day with same stream/topic
            def parse_d(s: str) -> datetime:
                return datetime.fromisoformat(s) if "T" in s else datetime.strptime(s, "%Y-%m-%d")

            bday = parse_d(base["day"]).date()
            topic_code = base["topic_code"]
            topic_id = base["topic_id"]
            stream_id = base["stream_id"]

            # join topics if needed
            title = ""
            ann = ""
            if not topic_code and topic_id is not None and _table_exists(con, "topics"):
                t = con.execute("SELECT code AS topic_code, title, annotation FROM topics WHERE id=?",
                                (topic_id,)).fetchone()
                if t:
                    topic_code = t["topic_code"]
                    title = t["title"] or ""
                    ann = t["annotation"] or ""

            # previous day
            prev = con.execute(
                f"SELECT {day_col} AS day FROM session_days WHERE date({day_col})=date(?)"
                + (f" AND {stream_col}=?" if stream_col else "")
                + (f" AND {topic_code_col}=?" if topic_code_col else (f" AND {topic_id_col}=?" if topic_id_col else ""))
                + " LIMIT 1",
                tuple([ (bday - timedelta(days=1)).isoformat() ] +
                      ([stream_id] if stream_col else []) +
                      ([topic_code] if topic_code_col else ([topic_id] if topic_id_col else []))
                ),
            ).fetchone()
            start_date = (bday - timedelta(days=1)) if prev else bday

            # next day
            nxt = con.execute(
                f"SELECT {day_col} AS day FROM session_days WHERE date({day_col})=date(?)"
                + (f" AND {stream_col}=?" if stream_col else "")
                + (f" AND {topic_code_col}=?" if topic_code_col else (f" AND {topic_id_col}=?" if topic_id_col else ""))
                + " LIMIT 1",
                tuple([ (bday + timedelta(days=1)).isoformat() ] +
                      ([stream_id] if stream_col else []) +
                      ([topic_code] if topic_code_col else ([topic_id] if topic_id_col else []))
                ),
            ).fetchone()
            end_date = (bday + timedelta(days=1)) if nxt else bday

            return {
                "id": int(base["id"]),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "topic_code": topic_code,
                "title": title,
                "annotation": ann,
            }

    return None
