
from __future__ import annotations

import logging
from .core import get_db_connection

log = logging.getLogger(__name__)

def ensure_schedule_schema() -> None:
    """
    Создаёт (если нет) таблицы topics и session_days.
    Ничего не сидирует — только схема.
    """
    with get_db_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                title TEXT,
                annotation TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS session_days (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,        -- YYYY-MM-DD
                stream_id INTEGER,
                topic_id INTEGER,
                topic_code TEXT,
                UNIQUE(date, stream_id)
            )
            """
        )
        con.commit()
        log.info("[SCHEMA] topics/session_days ensured")
