# crm2/db/auto_migrate.py
# Назначение: Автоматическое создание и миграция схемы базы данных (таблицы: topics, sessions, events, healing_sessions, user_flags, attendance, payments)
# Функции:
# - _exec - Вспомогательная функция для выполнения SQL-запроса
# - _has_column - Проверяет наличие столбца в таблице
# - ensure_topics_and_session_days - Создает таблицы topics и sessions (с авто-миграцией для добавления cohort_id)
# - ensure_events_and_healings - Создает таблицы events и healing_sessions
# - ensure_user_flags_and_attendance - Создает таблицы user_flags, attendance и payments
# - ensure_schedule_schema - Публичная точка входа для создания базовых таблиц расписания (устаревшее, для обратной совместимости)
# - ensure_all_schemas - Единая точка для создания всех необходимых таблиц (вызывается при старте бота)
# === Автогенерированный заголовок: crm2/db/auto_migrate.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: _exec, _has_column, ensure_topics_and_session_days, ensure_events_and_healings, ensure_user_flags_and_attendance, ensure_schedule_schema, ensure_all_schemas
# === Конец автозаголовка
# crm2/db/auto_migrate.py
from __future__ import annotations

import logging
import sqlite3
from .core import get_db_connection

log = logging.getLogger(__name__)


def _exec(con: sqlite3.Connection, sql: str) -> None:
    """Вспомогательный безопасный EXEC (без несуществующих cur)."""
    con.execute(sql)


def _has_column(con: sqlite3.Connection, table: str, col: str) -> bool:
    cur = con.execute(f"PRAGMA table_info({table});")
    return any(row[1] == col for row in cur.fetchall())


# -------------------------------
#  БАЗОВЫЕ ТАБЛИЦЫ РАСПИСАНИЯ
# -------------------------------

def ensure_topics_and_session_days(con: sqlite3.Connection) -> None:
    # topics
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

    # sessions (целевая схема уже с cohort_id)
    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date  TEXT NOT NULL,
            end_date    TEXT,
            topic_code  TEXT,
            title       TEXT,
            annotation  TEXT,
            cohort_id   INTEGER
        );
        """,
    )

    # ── авто-миграция старой базы: добавить cohort_id и перенести из cohort_id ──
    try:
        if not _has_column(con, "sessions", "cohort_id"):
            con.execute("ALTER TABLE sessions ADD COLUMN cohort_id INTEGER;")
        if _has_column(con, "sessions", "cohort_id"):
            con.execute(
                """
                UPDATE sessions
                SET cohort_id = cohort_id
                WHERE cohort_id IS NULL AND cohort_id IS NOT NULL;
                """
            )
    except sqlite3.OperationalError:
        # на всякий случай не роняем старт
        pass

    # индексы (создаём нужные, старые удаляем — и тоже не роняем)
    try:
        con.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_date);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_sessions_cohort_start ON sessions(cohort_id, start_date);")
        con.execute("DROP INDEX IF EXISTS idx_sessions_cohort_start;")
    except sqlite3.OperationalError:
        pass


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

    _exec(
        con,
        """
        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            session_id  INTEGER NOT NULL,
            paid        INTEGER NOT NULL CHECK (paid IN (0,1)),
            noted_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            noted_by    INTEGER
        );
        """,
    )
    _exec(
        con,
        "CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, session_id);",
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
