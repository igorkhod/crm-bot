# === Файл: crm2/db/sessions.py
from __future__ import annotations

import logging
import sqlite3
from typing import Dict
from typing import Optional

from .core import get_db_connection  # используем фабрику подключения


def get_user_stream_info_by_tg(tg_id: int) -> Optional[dict]:
    """
    Возвращает dict со значениями:
      - stream_id: int
      - stream_code: str  (берём s.code | s.title | s.name | str(id) — что есть)
    Никаких жёстких ссылок на несуществующие колонки!
    """
    con = get_db_connection()
    try:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            """
            SELECT s.id AS stream_id, s.*
            FROM participants p
                     JOIN users u ON u.id = p.user_id
                     LEFT JOIN streams s ON s.id = p.stream_id
            WHERE u.telegram_id = ?
            ORDER BY p.id DESC LIMIT 1
            """,
            (tg_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        # аккуратно формируем человекочитаемый код потока
        stream_code = d.get("code") or d.get("title") or d.get("name") or str(d["stream_id"])
        return {"stream_id": d["stream_id"], "stream_code": stream_code}
    finally:
        con.close()


def get_user_stream_code_by_tg(tg_id: int) -> Optional[str]:
    info = get_user_stream_info_by_tg(tg_id)
    return info["stream_code"] if info else None


def get_user_stream(conn: sqlite3.Connection, tg_id: int) -> Optional[sqlite3.Row]:
    cur = conn.execute(
        """
        SELECT s.id                          AS stream_id,
               COALESCE(s.code, s.title, '') AS stream_code
        FROM participants p
                 JOIN users u ON u.id = p.user_id
                 LEFT JOIN streams s ON s.id = p.stream_id
        WHERE u.telegram_id = ?
        ORDER BY p.id DESC LIMIT 1
        """,
        (tg_id,),
    )
    return cur.fetchone()


def get_user_stream_code_by_tg(tg_id: int) -> Optional[str]:
    con = get_db_connection()
    try:
        con.row_factory = sqlite3.Row
        row = get_user_stream(con, tg_id)
        return (row["stream_code"] if row else None)
    finally:
        con.close()


def get_user_stream(conn: sqlite3.Connection, tg_id: int) -> Optional[sqlite3.Row]:
    """
    Возвращает строку с полями: stream_id, stream_code (например: 'ППТ-2')
    для заданного Telegram ID (tg_id). Берём последний (актуальный) поток из participants.
    """
    cur = conn.execute(
        """
        SELECT s.id                          AS stream_id,
               COALESCE(s.code, s.title, '') AS stream_code
        FROM participants p
                 JOIN users u ON u.id = p.user_id
                 LEFT JOIN streams s ON s.id = p.stream_id
        WHERE u.telegram_id = ?
        ORDER BY p.id DESC LIMIT 1
        """,
        (tg_id,),
    )
    return cur.fetchone()


def get_user_stream_code_by_tg(tg_id: int) -> Optional[str]:
    con = get_db_connection()
    try:
        # row_factory уже обычно проставлен в get_db_connection,
        # но на всякий случай можно раскомментировать следующую строку:
        # con.row_factory = sqlite3.Row
        row = get_user_stream(con, tg_id)
        return (row["stream_code"] if row else None)
    finally:
        con.close()


def _detect_table_name(cur) -> Optional[str]:
    cur.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                  AND name IN (
                               'events_xlsx', 'events_ui', 'v_upcoming_days', 'session_index',
                               'sessions', 'schedule', 'events'
                    )
                ORDER BY CASE name
                             WHEN 'events_xlsx' THEN 1
                             WHEN 'events_ui' THEN 2
                             WHEN 'v_upcoming_days' THEN 3
                             WHEN 'session_index' THEN 4
                             WHEN 'sessions' THEN 5
                             WHEN 'schedule' THEN 6
                             WHEN 'events' THEN 7
                             ELSE 99 END LIMIT 1
                """)
    row = cur.fetchone()
    return row["name"] if row else None


def _select_upcoming_sql(table: str) -> str:
    # Источники, где уже есть start_date/end_date
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
    # Таблица events: есть только date → делаем алиасы
    if table == "events":
        return """
               SELECT id,
                      start_date,
                      end_date,
                      ''                  AS topic_code,
                      COALESCE(title, '') AS title,
                      ''                  AS annotation
               FROM (SELECT id,
                            CASE
                                WHEN date LIKE '__.__.____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         WHEN date LIKE '__-__-____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         ELSE substr(date, 1, 10)
                         END AS start_date, CASE
                         WHEN date LIKE '__.__.____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         WHEN date LIKE '__-__-____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         ELSE substr(date, 1, 10)
                         END AS end_date, title
                     FROM events)
               WHERE DATE (start_date) >= DATE ('now')
               ORDER BY DATE (start_date) ASC
                   LIMIT ? \
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
               SELECT id,
                      start_date,
                      end_date,
                      ''                  AS topic_code,
                      COALESCE(title, '') AS title,
                      ''                  AS annotation
               FROM (SELECT id,
                            CASE
                                WHEN date LIKE '__.__.____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         WHEN date LIKE '__-__-____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         ELSE substr(date, 1, 10)
                         END AS start_date, CASE
                         WHEN date LIKE '__.__.____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         WHEN date LIKE '__-__-____'
                         THEN substr(date, 7, 4)||'-'||substr(date, 4, 2)||'-'||substr(date, 1, 2)
                         ELSE substr(date, 1, 10)
                         END AS end_date, title
                     FROM events)
               WHERE id = ? LIMIT 1 \
               """
    raise ValueError(f"Unknown schedule source: {table}")


import asyncio


async def get_upcoming_sessions(limit: int = 5, tg_id: Optional[int] = None):
    def _q():
        con = get_db_connection()
        try:
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            table = _detect_table_name(cur)
            if not table:
                return []

            stream_id = None
            source_pat = None
            if tg_id is not None:
                info = get_user_stream_info_by_tg(tg_id)
                if info:
                    stream_id = info["stream_id"]
                    # для Excel-файлов фильтруем по «..._2_...» и т.п.
                    source_pat = f"%_{stream_id}_%"

            sql = _select_upcoming_sql(table)
            params = []

            if table == "events_xlsx" and source_pat:
                sql = sql.replace(
                    "WHERE DATE(start_date) >= DATE('now')",
                    "WHERE DATE(start_date) >= DATE('now') AND source_file LIKE ?",
                    1,
                )
                params.append(source_pat)
            elif table == "events" and stream_id:
                sql = sql.replace(
                    "WHERE DATE(start_date) >= DATE('now')",
                    "WHERE DATE(start_date) >= DATE('now') AND stream_id = ?",
                    1,
                )
                params.append(stream_id)

            params.append(limit)
            cur.execute(sql, tuple(params))
            return [dict(r) for r in cur.fetchall()]
        finally:
            con.close()

    return await asyncio.to_thread(_q)


async def get_session_by_id(session_id: int) -> Optional[Dict]:
    def _q():
        con = get_db_connection()
        try:
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
