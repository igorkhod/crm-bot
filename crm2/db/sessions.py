# crm2\db\sessions.py

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .core import get_db_connection


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


def _safe_title_from_table(con: sqlite3.Connection, table: str, id_value: int) -> Optional[str]:
    if not _table_exists(con, table):
        return None
    cols = _cols(con, table)
    id_col = _pick(cols, ["id", f"{table}_id"]) or "id"
    title_col = _pick(cols, ["title", "name", "code", "label"])
    if not title_col:
        return None
    row = con.execute(
        f"SELECT {title_col} AS title FROM {table} WHERE {id_col}=? LIMIT 1", (id_value,)
    ).fetchone()
    return (row["title"] if row and "title" in row.keys() else None)


def get_user_cohort_title_by_tg(tg_id: int) -> Tuple[Optional[int], Optional[str]]:
    return None, "⏸️ Временно недоступно"
    """
    Возвращает (cohort_id, заголовок потока) по telegram_id пользователя.
    Используем users.cohort_id. Если таблица cohorts существует — берём title оттуда,
    иначе возвращаем дефолтную подпись по словарю.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        u = con.execute(
            "SELECT cohort_id FROM users WHERE telegram_id=? LIMIT 1",
            (tg_id,),
        ).fetchone()

    if not u or u["cohort_id"] in (None, ""):
        return None, None

    cohort_id = int(u["cohort_id"])

    # если есть таблица cohorts — тянем подпись оттуда
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        title = _safe_title_from_table(con, "cohorts", cohort_id)

    if not title:
        titles = {
            1: "1 поток · набор 09.2023",
            2: "2 поток · набор 04.2025",
        }
        title = titles.get(cohort_id, f"Поток {cohort_id}")

    return cohort_id, title



def _select_from_session_days(con: sqlite3.Connection, *, cohort_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    cols = _cols(con, "session_days")
    id_col = "id"
    day_col = _pick(cols, ["day", "date", "day_date", "session_day"]) or "date"
    cohort_col = _pick(cols, ["cohort_id", "cohort_id"])
    topic_code_col = _pick(cols, ["topic_code", "code"])
    topic_id_col = _pick(cols, ["topic_id"])

    where = f"date({day_col}) >= date('now')"
    params: List[Any] = []
    if cohort_id is not None and cohort_col is not None:
        where += f" AND {cohort_col}=?"
        params.append(cohort_id)

    select_cols = [f"{id_col} AS id", f"{day_col} AS day"]
    if topic_code_col:
        select_cols.append(f"{topic_code_col} AS topic_code")
    else:
        select_cols.append("NULL AS topic_code")
    if topic_id_col:
        select_cols.append(f"{topic_id_col} AS topic_id")
    else:
        select_cols.append("NULL AS topic_id")

    if cohort_col:
        select_cols.append(f"{cohort_col} AS cohort_id")
    else:
        select_cols.append("NULL AS cohort_id")

    sql = f"SELECT {', '.join(select_cols)} FROM session_days WHERE {where} ORDER BY {day_col}"
    rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    if not rows:
        return []

    topics_by_id: Dict[int, Dict[str, str]] = {}
    topics_by_code: Dict[str, Dict[str, str]] = {}
    if _table_exists(con, "topics"):
        for tr in con.execute("SELECT id, code, title, annotation FROM topics").fetchall():
            rec = {
                "topic_code": tr["code"],
                "title": tr["title"] or "",
                "annotation": tr["annotation"] or "",
            }
            topics_by_id[int(tr["id"])] = rec
            if tr["code"]:
                topics_by_code[str(tr["code"])] = rec

    def parse_d(s: str) -> datetime.date:
        return datetime.fromisoformat(s).date() if "T" in s else datetime.strptime(s, "%Y-%m-%d").date()

    items = []
    for r in rows:
        d = parse_d(r["day"])
        code = r.get("topic_code")
        title = ""
        ann = ""

        tinfo = None
        tid = r.get("topic_id")
        if tid is not None:
            tinfo = topics_by_id.get(int(tid))
        if (not tinfo) and code:
            tinfo = topics_by_code.get(str(code))

        if tinfo:
            code = tinfo.get("topic_code") or code
            title = tinfo.get("title") or ""
            ann = tinfo.get("annotation") or ""

        items.append({
            "id": int(r["id"]),
            "day": d,
            "cohort_id": r.get("cohort_id"),
            "topic_code": code,
            "title": title,
            "annotation": ann,
        })

    items.sort(key=lambda x: x["day"])

    groups: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None
    from datetime import timedelta as _td

    for it in items:
        if cur is None:
            cur = {
                "id": it["id"],
                "start_date": it["day"].isoformat(),
                "end_date": it["day"].isoformat(),
                "topic_code": it["topic_code"],
                "title": it["title"],
                "annotation": it["annotation"],
                "cohort_id": it["cohort_id"],
            }
            continue

        prev_end = datetime.fromisoformat(cur["end_date"]).date()
        if (it["day"] - prev_end) == _td(days=1):
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
                "cohort_id": it["cohort_id"],
            }

    if cur is not None:
        groups.append(cur)

    groups = groups[:limit]

    # Оставляем cohort_id, чтобы в UI можно было показывать поток
    cleaned = []
    for g in groups:
        cleaned.append({
            "id": g["id"],
            "start_date": g["start_date"],
            "end_date": g["end_date"],
            "topic_code": g.get("topic_code"),
            "title": g.get("title"),
            "annotation": g.get("annotation"),
            "cohort_id": g.get("cohort_id"),
        })
    return cleaned


def _select_from_sessions(con: sqlite3.Connection, *, cohort_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    cols = _cols(con, "sessions")
    id_col = "id"
    start_col = _pick(cols, ["start_date", "start", "date"])
    end_col = _pick(cols, ["end_date", "end", "date"])
    topic_col = _pick(cols, ["topic_code", "code", "topic"])
    title_col = _pick(cols, ["title", "name"])
    ann_col = _pick(cols, ["annotation", "ann", "description", "desc"])
    cohort_col = _pick(cols, ["cohort_id", "cohort_id"])

    if start_col is None:
        raise RuntimeError("Table 'sessions' has no start_date/start/date column")

    where = f"date({start_col}) >= date('now')"
    params: List[Any] = []
    if cohort_id is not None and cohort_col is not None:
        where += f" AND {cohort_col}=?"
        params.append(cohort_id)

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


def _select_from_events(con: sqlite3.Connection, *, cohort_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    cols = _cols(con, "events")
    id_col = "id"
    date_col = _pick(cols, ["date", "event_date", "start", "start_date"]) or "date"
    title_col = _pick(cols, ["title", "name"])
    ann_col = _pick(cols, ["annotation", "ann", "description", "desc"])
    cohort_col = _pick(cols, ["cohort_id", "cohort_id"])

    where = f"date({date_col}) >= date('now')"
    params: List[Any] = []
    if cohort_id is not None and cohort_col is not None:
        where += f" AND {cohort_col}=?"
        params.append(cohort_id)

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
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        cohort_id = None
        if tg_id is not None:
            row = con.execute(
                """
                WITH u AS (SELECT id, cohort_id
                           FROM users
                           WHERE telegram_id = ?
                    LIMIT 1
                    )
                   , p AS (
                SELECT cohort_id
                FROM participants
                WHERE user_id=(SELECT id FROM u LIMIT 1)
                ORDER BY id DESC
                    LIMIT 1
                    )
                SELECT COALESCE(p.cohort_id, u.cohort_id) AS cohort_id
                FROM u
                         LEFT JOIN p ON 1 = 1
                """,
                (tg_id,),
            ).fetchone()
            if row and row["cohort_id"] not in (None, ""):
                cohort_id = int(row["cohort_id"])

        if _table_exists(con, "sessions"):
            return _select_from_sessions(con, cohort_id=cohort_id, limit=limit)
        if _table_exists(con, "events"):
            return _select_from_events(con, cohort_id=cohort_id, limit=limit)
        if _table_exists(con, "session_days"):
            return _select_from_session_days(con, cohort_id=cohort_id, limit=limit)
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

        if _table_exists(con, "session_days"):
            cols = _cols(con, "session_days")
            id_col = "id"
            day_col = _pick(cols, ["day", "date", "day_date", "session_day"]) or "date"
            topic_code_col = _pick(cols, ["topic_code", "code"])
            topic_id_col = _pick(cols, ["topic_id"])

            base = con.execute(
                f"SELECT {id_col} AS id, {day_col} AS day, "
                f"{(topic_code_col + ' AS topic_code') if topic_code_col else 'NULL AS topic_code'}, "
                f"{(topic_id_col + ' AS topic_id') if topic_id_col else 'NULL AS topic_id'} "
                f"FROM session_days WHERE {id_col}=? LIMIT 1",
                (session_id,),
            ).fetchone()
            if not base:
                return None

            def parse_d(s: str) -> datetime.date:
                return datetime.fromisoformat(s).date() if "T" in s else datetime.strptime(s, "%Y-%m-%d").date()

            bday = parse_d(base["day"])
            topic_code = base["topic_code"]
            topic_id = base["topic_id"]

            title = ""
            ann = ""
            if _table_exists(con, "topics"):
                if topic_id is not None:
                    t = con.execute("SELECT code, title, annotation FROM topics WHERE id=?",
                                    (topic_id,)).fetchone()
                elif topic_code is not None:
                    t = con.execute("SELECT code, title, annotation FROM topics WHERE code=?",
                                    (topic_code,)).fetchone()
                else:
                    t = None
                if t:
                    topic_code = t["code"] or topic_code
                    title = t["title"] or ""
                    ann = t["annotation"] or ""

            prev = con.execute(f"SELECT 1 FROM session_days WHERE date({day_col})=date(?) LIMIT 1",
                               ((bday - timedelta(days=1)).isoformat(),)).fetchone()
            nxt = con.execute(f"SELECT 1 FROM session_days WHERE date({day_col})=date(?) LIMIT 1",
                              ((bday + timedelta(days=1)).isoformat(),)).fetchone()

            start_date = (bday - timedelta(days=1)).isoformat() if prev else bday.isoformat()
            end_date = (bday + timedelta(days=1)).isoformat() if nxt else bday.isoformat()

            return {
                "id": int(base["id"]),
                "start_date": start_date,
                "end_date": end_date,
                "topic_code": topic_code,
                "title": title,
                "annotation": ann,
            }

    return None


def get_upcoming_sessions_by_cohort(cohort_id: int, limit: int = 5) -> list[dict]:
    return []  # ⏸️ Временно отключено до исправления базы

    """
    Вернёт список ближайших занятий только для указанного потока.
    Использует ту же логику, что и get_upcoming_sessions, но cohort_id задаётся явно.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        if _table_exists(con, "sessions"):
            return _select_from_sessions(con, cohort_id=cohort_id, limit=limit)
        if _table_exists(con, "events"):
            return _select_from_events(con, cohort_id=cohort_id, limit=limit)
        if _table_exists(con, "session_days"):
            return _select_from_session_days(con, cohort_id=cohort_id, limit=limit)
        return []


def get_nearest_session_text() -> str | None:
    """
    Короткая строка «Ближайшее занятие: 13.09.2025 — 14.09.2025 • ПТГ-2».
    Берём самое раннее занятие независимо от потока.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        # Попробуем через session_days, т.к. там точнее даты
        if _table_exists(con, "session_days") and _table_exists(con, "topics"):
            cur = con.execute("""
                              SELECT MIN(sd.date) AS start_date,
                                     MAX(sd.date) AS end_date,
                                     t.code       AS topic_code
                              FROM session_days sd
                                       JOIN topics t ON t.id = sd.topic_id
                              WHERE date (sd.date) >= date ('now')
                              GROUP BY t.code
                              ORDER BY date (start_date)
                                  LIMIT 1
                              """)
            row = cur.fetchone()
            if row:
                s = row["start_date"]
                e = row["end_date"]
                code = row["topic_code"] or ""
                if s and e and s != e:
                    dates = f"{s} — {e}"
                else:
                    dates = s or e or "—"
                return f"Ближайшее занятие: {dates} • {code}"
        return None


def get_recent_past_sessions_by_cohort(cohort_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    return []  # ⏸️ Временно отключено до исправления базы
    """
    Последние прошедшие занятия потока (по start_date <= today), новее – выше.
    """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """
            SELECT id, start_date, end_date, topic_code, title, annotation, cohort_id
            FROM sessions
            WHERE cohort_id = ? AND DATE (start_date) <= DATE ('now')
            ORDER BY DATE (start_date) DESC
                LIMIT ?
            """,
            (cohort_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

# конец файла # crm2\db\sessions.py
