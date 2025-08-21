# === Файл: crm2/db/sessions.py
from __future__ import annotations
import asyncio
from typing import Optional
from .core import get_db_connection

async def get_upcoming_sessions(limit: int = 5) -> list[dict]:
    def _q():
        con = get_db_connection()
        cur = con.cursor()
        cur.execute(
            """
            SELECT id, start_date, end_date, topic_code, title, annotation
            FROM events
            WHERE date(start_date) >= date('now')
            ORDER BY start_date ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return rows
    return await asyncio.to_thread(_q)

async def get_session_by_id(session_id: int) -> Optional[dict]:
    def _q():
        con = get_db_connection()
        cur = con.cursor()
        cur.execute(
            """
            SELECT id, start_date, end_date, topic_code, title, annotation
            FROM events
            WHERE id = ?
            """,
            (session_id,),
        )
        row = cur.fetchone()
        con.close()
        return dict(row) if row else None
    return await asyncio.to_thread(_q)
