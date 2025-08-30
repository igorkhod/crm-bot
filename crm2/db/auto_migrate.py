# crm2/db/auto_migrate.py
from __future__ import annotations

import logging
import sqlite3
from .core import get_db_connection

log = logging.getLogger(__name__)


def _exec(con: sqlite3.Connection, sql: str) -> None:
    """Вспомогательный безопасный EXEC (без несуществующих cur)."""
    con.execute(sql)


# -------------------------------
#  БАЗОВЫЕ ТАБЛИЦЫ РАСПИСАНИЯ
# -------------------------------
def ensure_topics_and_session_days(con: sqlite3.Connection) -> None:
    """
    Создаёт таблицы topics и sessions (унифицированная таблица занятий).
    Ранее могла называться session_days — оставляем совместимость индексами.
    """
    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS topics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT UNIQUE,
            title       TEXT,
            annotation  TEXT
        );
        """,
    )

    # Единая таблица занятий (используется в crm2/db/sessions.py как FROM sessions)
    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date  TEXT NOT NULL,          -- YYYY-MM-DD
            end_date    TEXT,                   -- YYYY-MM-DD (может совпадать со start_date)
            topic_code  TEXT,                   -- ссылка на topics.code
            title       TEXT,
            annotation  TEXT,
            stream_id   INTEGER                 -- номер потока (1/2/…)
        );
        """,
    )

    _exec(con, "CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_date);")
    _exec(
        con,
        "CREATE INDEX IF NOT EXISTS idx_sessions_stream_start ON sessions(stream_id, start_date);",
    )


# ---------------------------------------
#  ДОП. ТАБЛИЦЫ: СОБЫТИЯ И СЕССИИ-«ХИЛИНГ»
# ---------------------------------------
def ensure_events_and_healings(con: sqlite3.Connection) -> None:
    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            start_date  TEXT NOT NULL,          -- YYYY-MM-DD
            end_date    TEXT,                   -- YYYY-MM-DD
            note        TEXT
        );
        """,
    )
    _exec(
        con,
        "CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_date);",
    )

    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS healing_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,          -- YYYY-MM-DD
            time_start  TEXT NOT NULL,          -- HH:MM
            note        TEXT
        );
        """,
    )
    _exec(
        con,
        "CREATE INDEX IF NOT EXISTS idx_healings_dt ON healing_sessions(date, time_start);",
    )


# ---------------------------------------
#  ДОП. ТАБЛИЦЫ: ФЛАГИ И ПОСЕЩАЕМОСТЬ
# ---------------------------------------
def ensure_user_flags_and_attendance(con: sqlite3.Connection) -> None:
    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS user_flags (
            user_id         INTEGER PRIMARY KEY,
            notify_enabled  INTEGER DEFAULT 1
        );
        """,
    )

    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            session_id  INTEGER NOT NULL,
            status      TEXT NOT NULL CHECK (status IN ('present','absent','late')),
            noted_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            noted_by    INTEGER
        );
        """,
    )
    _exec(
        con,
        "CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id, session_id);",
    )


# ---------------------------------------
#  ПУБЛИЧНЫЕ ТОЧКИ ВХОДА
# ---------------------------------------
def ensure_schedule_schema() -> None:
    """
    Поддержка старого имени: создаёт базовые таблицы расписания.
    """
    with get_db_connection() as con:
        ensure_topics_and_session_days(con)
        con.commit()


def ensure_all_schemas() -> None:
    """
    Единая точка: создаём всё, что нужно боту.
    Вызывается при старте.
    """
    log.info("[SCHEMA] topics/session_days/events/healings ensured")
    with get_db_connection() as con:
        ensure_topics_and_session_days(con)
        ensure_events_and_healings(con)
        ensure_user_flags_and_attendance(con)
        con.commit()
