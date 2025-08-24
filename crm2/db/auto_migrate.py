
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


def apply_topic_overrides(overrides: dict[str, dict[str, str]]) -> None:
    """
    Совместимость с app.py: точечно правит title/annotation по коду темы.
    Идемпотентно: безопасно вызывать при каждом старте.
    """
    if not overrides:
        return
    with get_db_connection() as con:
        cur = con.cursor()
        # Убедимся, что таблица есть (на случай старта «с нуля»)
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
        for code, fields in overrides.items():
            if "title" in fields:
                cur.execute("UPDATE topics SET title=? WHERE code=?", (fields["title"], code))
            if "annotation" in fields:
                cur.execute("UPDATE topics SET annotation=? WHERE code=?", (fields["annotation"], code))
        con.commit()
        log.info("[OVERRIDES] topics updated: %s", ", ".join(overrides.keys()))
