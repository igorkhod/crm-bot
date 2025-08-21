# === crm2/db/sessions.py ===
from __future__ import annotations

import asyncio
import logging
import sqlite3
from typing import Dict, Optional

from .core import get_db_connection


# ---------- Потоки пользователя ----------

def get_user_stream_info_by_tg(tg_id: int) -> Optional[dict]:
    """
    Возвращает dict:
      - stream_id: int
      - stream_code: str  (берём s.code | s.title | s.name | str(id) — что есть)
    Без жёсткой зависимости от колонки s.code.
    """
    con = get_db_connection()
    try:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            """
            SELECT s.id AS stream_id, s.*
            FROM participants p
            JOIN users u       ON u.id = p.user_id
            LEFT JOIN streams s ON s.id = p.stream_id
            WHERE u.telegram_id = ?
            ORDER BY p.id DESC
            LIMIT 1
            """,
            (tg_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        stream_id = d.get("stream_id")
        stream_code = d.get("code") or d.get("title") or d.get("name") or (str(stream_id) if stream_id else None)
        return {"stream_id": stream_id, "stream_code": stream_code}
    finally:
        con.close()


def get_user_stream_code_by_tg(tg_id: int) -> Optional[str]:
    info = get_user_stream_info_by_tg(tg_id)
    return info["stream_code"] if info else None


# ---------- Определение источника расписания ----------

def _detect_table_name(cur: sqlite3.Cursor) -> Optional[str]:
    cur.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table','view')
          AND name IN (
            'events_xlsx','events_ui','v_upcoming_days','session_index',
            'sessions','schedule','events'
          )
        ORDER BY CASE name
                   WHEN 'events_xlsx'     THEN 1
                   WHEN 'events_ui'       THEN 2
                   WHEN 'v_upcoming_days' THEN 3
                   WHEN 'session_index'   THEN 4
                   WHEN 'sessions'        THEN 5
                   WHEN 'schedule'        THEN 6
                   WHEN 'events'          THEN 7
                   ELSE 99
                 END
        LIMIT 1
        """
    )
    r = cur.fetchone()
    return r["name"] if r else None


def _select_upcoming_sql(table: str) -> str:
    """SQL для списка ближайших сессий для разных источников."""
    if table in ("events_ui", "events_xlsx", "v_upcoming_days", "session_index", "sessions", "schedule"):
        return f"""
            SELECT id, start_date, end_date,
                   COALESCE(topic_code, '') AS topic_code,
                   COALESCE(title, '')      AS title,
                   COALESCE(annotation, '') AS annotation
            FROM {table}
            WHERE DATE(start_date) >= DATE('now')
            ORDER BY DATE(start_date) ASC
            LIMIT ?
        """
    if table == "events":
        # В events только date: нормализуем в start/end
        return """
            SELECT id, start_date, end_date,
                   ''                  AS topic_code,
                   COALESCE(title, '') AS title,
                   ''                  AS annotation
            FROM (
                SELECT id,
                       CASE
                         WHEN date LIKE '__.__.____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         WHEN date LIKE '__-__-____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         ELSE substr(date,1,10)
                       END AS start_date,
                       CASE
                         WHEN date LIKE '__.__.____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         WHEN date LIKE '__-__-____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         ELSE substr(date,1,10)
                       END AS end_date,
                       title
                FROM events
            )
            WHERE DATE(start_date) >= DATE('now')
            ORDER BY DATE(start_date) ASC
            LIMIT ?
        """
    raise ValueError(f"Unknown schedule source: {table}")


def _select_by_id_sql(table: str) -> str:
    if table in ("events_ui", "events_xlsx", "v_upcoming_days", "session_index", "sessions", "schedule"):
        return f"""
            SELECT id, start_date, end_date,
                   COALESCE(topic_code, '') AS topic_code,
                   COALESCE(title, '')      AS title,
                   COALESCE(annotation, '') AS annotation
            FROM {table}
            WHERE id = ?
            LIMIT 1
        """
    if table == "events":
        return """
            SELECT id, start_date, end_date,
                   ''                  AS topic_code,
                   COALESCE(title, '') AS title,
                   ''                  AS annotation
            FROM (
                SELECT id,
                       CASE
                         WHEN date LIKE '__.__.____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         WHEN date LIKE '__-__-____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         ELSE substr(date,1,10)
                       END AS start_date,
                       CASE
                         WHEN date LIKE '__.__.____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         WHEN date LIKE '__-__-____'
                           THEN substr(date,7,4)||'-'||substr(date,4,2)||'-'||substr(date,1,2)
                         ELSE substr(date,1,10)
                       END AS end_date,
                       title
                FROM events
            )
            WHERE id = ?
            LIMIT 1
        """
    raise ValueError(f"Unknown schedule source: {table}")


# ---------- Публичные функции расписания ----------

async def get_upcoming_sessions(limit: int = 5, tg_id: Optional[int] = None):
    """Список ближайших занятий; при tg_id фильтруем под поток пользователя."""
    def _q():
        con = get_db_connection()
        try:
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            table = _detect_table_name(cur)
            if not table:
                return []

            stream_id: Optional[int] = None
            like_mask: Optional[str] = None
            if tg_id is not None:
                info = get_user_stream_info_by_tg(tg_id)
                if info:
                    stream_id = info["stream_id"]
                    # для Excel-файлов фильтруем по имени файла: ..._2_...
                    if stream_id:
                        like_mask = f"%_{stream_id}_%"

            sql = _select_upcoming_sql(table)
            params: list = []

            if table == "events_xlsx" and like_mask:
                sql = sql.replace(
                    "WHERE DATE(start_date) >= DATE('now')",
                    "WHERE DATE(start_date) >= DATE('now') AND source_file LIKE ?",
                    1,
                )
                params.append(like_mask)
            elif table == "events" and stream_id:
                # если в events есть колонка stream_id — сузим по ней (если нет, просто не сработает)
                try:
                    cur.execute("SELECT 1 FROM pragma_table_info('events') WHERE name='stream_id'")
                    if cur.fetchone():
                        sql = sql.replace(
                            "WHERE DATE(start_date) >= DATE('now')",
                            "WHERE DATE(start_date) >= DATE('now') AND stream_id = ?",
                            1,
                        )
                        params.append(stream_id)
                except Exception:
                    pass

            params.append(limit)
            cur.execute(sql, tuple(params))
            return [dict(r) for r in cur.fetchall()]
        finally:
            con.close()

    return await asyncio.to_thread(_q)


async def get_session_by_id(session_id: int) -> Optional[Dict]:
    """Детали занятия по id (из того же источника, что и список)."""
    def _q():
        con = get_db_connection()
        try:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            table = _detect_table_name(cur)
            if not table:
                logging.warning("[schedule] get_session_by_id: no table")
                return None
            cur.execute(_select_by_id_sql(table), (session_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            con.close()

    return await asyncio.to_thread(_q)
