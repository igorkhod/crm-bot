# === Автогенерированный заголовок: crm2/db/schedule_repo.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: _dicts, count_trainings, list_trainings, count_events, list_events, count_healings, list_healings, count_all, list_all
# === Конец автозаголовка
# crm2/db/schedule_repo.py
from typing import List, Dict, Any, Tuple
from sqlite3 import Row
from crm2.db.core import get_db_connection

def _dicts(rows: List[Row]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        k = set(r.keys())
        out.append({name: r[name] if name in k else None for name in r.keys()})
    return out

# ---------- ТРЕНИНГИ ПО ПОТОКАМ (session_days) ----------
def count_trainings(cohort_id: int) -> int:
    with get_db_connection() as con:
        cur = con.execute("SELECT COUNT(*) FROM session_days WHERE cohort_id = ?", (cohort_id,))
        return int(cur.fetchone()[0] or 0)

def list_trainings(cohort_id: int, offset: int, limit: int) -> List[Dict[str, Any]]:
    # подцепим title темы по topic_code или topic_id
    with get_db_connection() as con:
        con.row_factory = Row
        cur = con.execute("""
            SELECT sd.id,
                   sd.date,                 -- YYYY-MM-DD
                   sd.topic_code,
                   COALESCE(t.title, '') AS topic_title
            FROM session_days sd
            LEFT JOIN topics t
              ON (t.code = sd.topic_code) OR (t.id = sd.topic_id)
            WHERE sd.cohort_id = ?
            ORDER BY sd.date ASC, sd.id ASC
            LIMIT ? OFFSET ?
        """, (cohort_id, limit, offset))
        return _dicts(cur.fetchall())

# ---------- МЕРОПРИЯТИЯ (events) ----------
def count_events() -> int:
    with get_db_connection() as con:
        cur = con.execute("SELECT COUNT(*) FROM events")
        return int(cur.fetchone()[0] or 0)

def list_events(offset: int, limit: int) -> List[Dict[str, Any]]:
    with get_db_connection() as con:
        con.row_factory = Row
        cur = con.execute("""
            SELECT id, date, title, COALESCE(description, '') AS description
            FROM events
            ORDER BY date ASC, id ASC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return _dicts(cur.fetchall())

# ---------- ЦЕЛИТЕЛЬСКИЕ ПРИЁМЫ (healing_sessions) ----------
def count_healings() -> int:
    with get_db_connection() as con:
        cur = con.execute("SELECT COUNT(*) FROM healing_sessions")
        return int(cur.fetchone()[0] or 0)

def list_healings(offset: int, limit: int) -> List[Dict[str, Any]]:
    with get_db_connection() as con:
        con.row_factory = Row
        cur = con.execute("""
            SELECT id, date, time_start, COALESCE(note, '') AS note
            FROM healing_sessions
            ORDER BY date ASC, time_start ASC, id ASC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return _dicts(cur.fetchall())

# ---------- ОБЩЕЕ РАСПИСАНИЕ (всё вместе) ----------
def count_all() -> int:
    with get_db_connection() as con:
        cur = con.execute("""
            SELECT
              (SELECT COUNT(*) FROM session_days)
            + (SELECT COUNT(*) FROM events)
            + (SELECT COUNT(*) FROM healing_sessions)
        """)
        return int(cur.fetchone()[0] or 0)

def list_all(offset: int, limit: int) -> List[Dict[str, Any]]:
    with get_db_connection() as con:
        con.row_factory = Row
        cur = con.execute("""
            SELECT start_at, kind, title, details
            FROM (
                -- тренинги (дата без времени)
                SELECT sd.date || ' 00:00' AS start_at,
                       'training'           AS kind,
                       COALESCE(sd.topic_code,'') || CASE WHEN t.title IS NOT NULL AND t.title != '' THEN ' — ' || t.title ELSE '' END AS title,
                       'Поток: ' || CAST(sd.cohort_id AS TEXT) AS details
                FROM session_days sd
                LEFT JOIN topics t
                  ON (t.code = sd.topic_code) OR (t.id = sd.topic_id)

                UNION ALL
                -- мероприятия
                SELECT e.date || ' 00:00' AS start_at,
                       'event'             AS kind,
                       e.title             AS title,
                       COALESCE(e.description,'') AS details
                FROM events e

                UNION ALL
                -- целительские приёмы (есть время)
                SELECT h.date || ' ' || h.time_start AS start_at,
                       'healing'                   AS kind,
                       'Целительский приём'       AS title,
                       COALESCE(h.note,'')        AS details
                FROM healing_sessions h
            )
            ORDER BY start_at ASC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "start_at": r["start_at"],
                "kind": r["kind"],
                "title": r["title"],
                "details": r["details"],
            })
        return out
