import aiosqlite
import sqlite3  # используем для синхронной инициализации схемы
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "crm.db"


def init_db():
    """СИНХРОННАЯ инициализация схемы БД.
    Используем sqlite3, чтобы не требовались await/async при старте скрипта.
    Создаём таблицы:
      - visitors, sessions (сессии бота)
      - course_sessions (учебные двухдневные сессии)
      - VIEW session_days (дни учебных сессий)
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Таблица пользователей (визитёры)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT,
            first_seen TEXT
        )
    """)

    # Таблица сессий пользователей (бота)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (user_id) REFERENCES visitors (user_id)
        )
    """)

    # Гарантируем наличие столбца end_time
    cur.execute("PRAGMA table_info(sessions)")
    columns = [row[1] for row in cur.fetchall()]
    if "end_time" not in columns:
        cur.execute("ALTER TABLE sessions ADD COLUMN end_time TEXT")

    # === Учебные сессии потока (двухдневные) ===
    cur.execute("""
        CREATE TABLE IF NOT EXISTS course_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,                 -- уникальный ID учебной сессии
            cohort_id TEXT    NOT NULL,                           -- строковый идентификатор потока (например, 'recruitmen_2025_03')
            seq       INTEGER NOT NULL,                           -- порядковый номер сессии внутри потока
            course_kind TEXT  NOT NULL CHECK (course_kind IN ('ПН','ПТГ')), -- ПН=Психонетика, ПТГ=Психотехнологии гармонии
            title     TEXT    NOT NULL,                           -- человекочитаемое название
            date_start TEXT   NOT NULL,                           -- дата первого дня (YYYY-MM-DD)
            date_end   TEXT   NOT NULL,                           -- дата второго дня (YYYY-MM-DD)
            venue     TEXT    DEFAULT 'online',                   -- формат/место
            status    TEXT    NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','done','canceled')),
            notes     TEXT,                                       -- примечания
            created_at TEXT   DEFAULT (datetime('now'))           -- когда добавлено
        )
    """)

    # Индексы
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_course_sessions_cohort ON course_sessions(cohort_id)""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_course_sessions_dates  ON course_sessions(date_start, date_end)""")

    # VIEW по дням
    cur.execute("""
        CREATE VIEW IF NOT EXISTS session_days AS
        SELECT
            cs.id          AS session_id,
            cs.cohort_id   AS cohort_id,
            cs.seq         AS seq,
            cs.course_kind AS course_kind,
            cs.title       AS title,
            cs.date_start  AS date,
            1              AS day_no,
            cs.venue       AS venue,
            cs.status      AS status
        FROM course_sessions cs
        UNION ALL
        SELECT
            cs.id, cs.cohort_id, cs.seq, cs.course_kind, cs.title,
            cs.date_end, 2, cs.venue, cs.status
        FROM course_sessions cs
    """)

    conn.commit()
    conn.close()


def update_visitor(user_id: int, nickname: str):
    """Добавляет нового пользователя или обновляет его имя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM visitors WHERE user_id=?", (user_id,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO visitors (user_id, nickname, first_seen) VALUES (?, ?, ?)",
            (user_id, nickname, datetime.utcnow().isoformat()),
        )
    else:
        cur.execute("UPDATE visitors SET nickname=? WHERE user_id=?", (nickname, user_id))
    conn.commit()
    conn.close()


def start_session(user_id: int):
    """Открывает новую сессию"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (user_id, start_time) VALUES (?, ?)",
        (user_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def update_session(user_id: int):
    """Обновляет время последней сессии (end_time)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM sessions WHERE user_id=? ORDER BY start_time DESC LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        session_id = row[0]
        cur.execute(
            "UPDATE sessions SET end_time=? WHERE id=?",
            (datetime.utcnow().isoformat(), session_id),
        )
        conn.commit()
    conn.close()


def get_stats():
    """Возвращает статистику: (count, first_seen, session_count, first_session, total_seconds)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Кол-во пользователей и первый визит
    cur.execute("SELECT COUNT(*), MIN(first_seen) FROM visitors")
    count, first_seen = cur.fetchone()

    # Кол-во сессий и первая сессия
    cur.execute("SELECT COUNT(*), MIN(start_time) FROM sessions")
    session_count, first_session = cur.fetchone()

    # Суммарное время по всем сессиям
    cur.execute("SELECT start_time, end_time FROM sessions WHERE end_time IS NOT NULL")
    total_seconds = 0
    for start_time, end_time in cur.fetchall():
        try:
            st = datetime.fromisoformat(start_time)
            et = datetime.fromisoformat(end_time)
            total_seconds += (et - st).total_seconds()
        except Exception:
            pass

    conn.close()
    return count or 0, first_seen, session_count or 0, first_session, int(total_seconds)


async def get_user_by_nickname(nickname: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        async with db.execute("SELECT * FROM users WHERE nickname = ?", (nickname,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
