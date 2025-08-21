# === Файл: crm2/db/sessions.py
# Аннотация: DB-утилиты для расписания: ближайшие занятия и детальная карточка занятия.

from __future__ import annotations
import asyncio
import sqlite3
from pathlib import Path
from typing import Optional

# Если в проекте есть свой коннектор, подхватим его (например, get_db_connection()).
try:
    from .core import get_db_connection  # поменяй на свой модуль при необходимости
except Exception:
    get_db_connection = None  # fallback

# Путь к БД по умолчанию (если нет собственного коннектора)
DB_PATH = Path(__file__).resolve().parents[2] / "crm.db"

def _connect():
    if get_db_connection:
        return get_db_connection()
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con

async def get_upcoming_sessions(limit: int = 5) -> list[dict]:
    def _q():
        con = _connect()
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
        # Закрываем, только если использовали локальное подключение
        try:
            if not get_db_connection:
                con.close()
        except Exception:
            pass
        return rows
    return await asyncio.to_thread(_q)

async def get_session_by_id(session_id: int) -> Optional[dict]:
    def _q():
        con = _connect()
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
        try:
            if not get_db_connection:
                con.close()
        except Exception:
            pass
        return dict(row) if row else None
    return await asyncio.to_thread(_q)
