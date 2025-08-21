# === Файл: crm2/db/sessions.py
from __future__ import annotations
import asyncio
from typing import Optional, List, Dict
from .core import get_db_connection
import logging

def _detect_table_name(cur) -> Optional[str]:
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('events','sessions','schedule')
        ORDER BY CASE name
            WHEN 'events' THEN 1
            WHEN 'sessions' THEN 2
            WHEN 'schedule' THEN 3
            ELSE 99 END
        LIMIT 1
    """)
    row = cur.fetchone()
    return row["name"] if row else None

def _select_upcoming_sql(table: str) -> str:
    # Поддерживаем ISO 'YYYY-MM-DD' и 'YYYY-MM-DD HH:MM:SS'
    # Сравнение по DATE() в UTC (SQLite date('now')), для локали можно заменить на date('now','localtime')
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

def _select_by_id_sql(table: str) -> str:
    return f"""
        SELECT id, start_date, end_date,
               COALESCE(topic_code, '') AS topic_code,
               COALESCE(title, '')      AS title,
               COALESCE(annotation, '') AS annotation
        FROM {table}
        WHERE id = ?
        LIMIT 1
    """

async def get_upcoming_sessions(limit: int = 5) -> List[Dict]:
    def _q():
        con = get_db_connection()
        try:
            cur = con.cursor()
            table = _detect_table_name(cur)
            if not table:
                logging.warning("[schedule] no table found (expected: events/sessions/schedule)")
                return []
            cur.execute(_select_upcoming_sql(table), (limit,))
            rows = [dict(r) for r in cur.fetchall()]
            return rows
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
