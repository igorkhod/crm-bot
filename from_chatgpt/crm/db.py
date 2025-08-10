from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite  # остаётся для асинхронных выборок в боте

# Путь к базе CRM
DB_PATH = Path(__file__).parent / "crm.db"


# ===========================================================
# ИНИЦИАЛИЗАЦИЯ СХЕМЫ + СИДЫ (всё синхронно через sqlite3)
# ===========================================================
def init_db() -> None:
    """Создаёт/мигрирует схему и ИДЁМПОТЕНТНО наполняет её учебным расписанием.
    Делается синхронно (sqlite3), чтобы вызывать самой первой строкой в старте бота.
    Создаёт:
      - visitors, sessions
      - course_sessions (двухдневные учебные сессии, с уникальным ключом)
      - VIEW session_days (каждая учебная сессия разворачивается в 2 дня)
      - сидирует расписание потоков: 'recruitmen_2025_03' и '2023_09'
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ---------- 1) visitors ----------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS visitors (
            user_id     INTEGER PRIMARY KEY,
            nickname    TEXT,
            first_seen  TEXT
        )
        """
    )

    # ---------- 2) sessions (журнал сессий бота) ----------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            start_time TEXT,
            end_time   TEXT,
            FOREIGN KEY (user_id) REFERENCES visitors (user_id)
        )
        """
    )
    # Миграция столбца end_time (если таблица старая)
    cur.execute("PRAGMA table_info(sessions)")
    columns = [row[1] for row in cur.fetchall()]
    if "end_time" not in columns:
        cur.execute("ALTER TABLE sessions ADD COLUMN end_time TEXT")

    # ---------- 3) course_sessions (двухдневные учебные сессии) ----------
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS course_sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,                              -- уникальный ID
            cohort_id    TEXT    NOT NULL,                                              -- строковый идентификатор потока
            seq          INTEGER NOT NULL,                                              -- номер сессии в потоке
            course_kind  TEXT    NOT NULL CHECK (course_kind IN ('ПН','ПТГ')),          -- 'ПН' / 'ПТГ'
            title        TEXT    NOT NULL,                                              -- название
            date_start   TEXT    NOT NULL,                                              -- YYYY-MM-DD (день 1)
            date_end     TEXT    NOT NULL,                                              -- YYYY-MM-DD (день 2)
            venue        TEXT    DEFAULT 'online',
            status       TEXT    NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','done','canceled')),
            notes        TEXT,
            created_at   TEXT    DEFAULT (datetime('now')),
            UNIQUE(cohort_id, seq, course_kind)                                         -- защищает от дублей сидов
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_course_sessions_cohort ON course_sessions(cohort_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_course_sessions_dates  ON course_sessions(date_start, date_end)")

    # ---------- 4) VIEW: session_days ----------
    cur.execute(
        """
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
        """
    )

    # ---------- 5) СИДЫ (идёмпотентно) ----------
    def _ins(cohort_id: str, seq: int, kind: str, title: str, d1: str, d2: str) -> None:
        """INSERT OR IGNORE благодаря UNIQUE(cohort_id, seq, course_kind)."""
        cur.execute(
            "INSERT OR IGNORE INTO course_sessions (cohort_id, seq, course_kind, title, date_start, date_end) VALUES (?, ?, ?, ?, ?, ?)",
            (cohort_id, seq, kind, title, d1, d2),
        )

    # 5a) Поток recruitmen_2025_03 (ПН + ПТГ)
    seed_2025 = [
        (1,  "ПН",  "Психонетика 1",               "2025-05-17", "2025-05-18"),
        (2,  "ПТГ", "Психотехнологии гармонии 2",  "2025-09-13", "2025-09-14"),
        (2,  "ПН",  "Психонетика 2",               "2025-10-25", "2025-10-26"),
        (3,  "ПТГ", "Психотехнологии гармонии 3",  "2025-12-06", "2025-12-07"),
        (3,  "ПН",  "Психонетика 3",               "2026-01-17", "2026-01-18"),
        (4,  "ПТГ", "Психотехнологии гармонии 4",  "2026-02-28", "2026-03-01"),
        (4,  "ПН",  "Психонетика 4",               "2026-04-11", "2026-04-12"),
        (5,  "ПН",  "Психонетика 5",               "2026-05-23", "2026-05-24"),
        (6,  "ПН",  "Психонетика 6",               "2026-07-04", "2026-07-05"),
        (7,  "ПН",  "Психонетика 7",               "2026-08-15", "2026-08-16"),
        (8,  "ПН",  "Психонетика 8",               "2026-09-26", "2026-09-27"),
        (9,  "ПН",  "Психонетика 9",               "2026-11-07", "2026-11-08"),
        (10, "ПН",  "Психонетика 10",              "2026-12-19", "2026-12-20"),
        (11, "ПН",  "Психонетика 11",              "2027-01-30", "2027-01-31"),
        (12, "ПН",  "Психонетика 12",              "2027-03-13", "2027-03-14"),
        (13, "ПН",  "Психонетика 13",              "2027-04-24", "2027-04-25"),
        (14, "ПН",  "Психонетика 14",              "2027-06-05", "2027-06-06"),
    ]
    for seq, kind, title, d1, d2 in seed_2025:
        _ins("recruitmen_2025_03", seq, kind, title, d1, d2)

    # 5b) Поток 2023_09 — актуальное расписание (ПН 10..14), второй день = +1 день
    items = [
        (10, "Психонетика 10", "2025-09-20"),
        (11, "Психонетика 11", "2025-11-01"),
        (12, "Психонетика 12", "2025-12-13"),
        (13, "Психонетика 13", "2026-01-24"),
        (14, "Психонетика 14", "2026-03-07"),
    ]
    for seq, title, d1 in items:
        d2 = (datetime.fromisoformat(d1) + timedelta(days=1)).date().isoformat()
        _ins("2023_09", seq, "ПН", title, d1, d2)

    conn.commit()
    conn.close()


# ===========================================================
# СИНХРОННЫЕ УТИЛИТЫ
# ===========================================================
def update_visitor(user_id: int, nickname: str) -> None:
    """Добавляет/обновляет запись в visitors."""
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


def start_session(user_id: int) -> None:
    """Открывает новую сессию пользователя (журнал активности)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (user_id, start_time) VALUES (?, ?)",
        (user_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def update_session(user_id: int) -> None:
    """Обновляет время последней сессии (end_time)."""
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


def get_stats() -> tuple[int, str | None, int, str | None, int]:
    """Возвращает агрегированную статистику по бот‑сессиям."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*), MIN(first_seen) FROM visitors")
    count, first_seen = cur.fetchone()

    cur.execute("SELECT COUNT(*), MIN(start_time) FROM sessions")
    session_count, first_session = cur.fetchone()

    cur.execute("SELECT start_time, end_time FROM sessions WHERE end_time IS NOT NULL")
    total_seconds = 0
    for start_time, end_time in cur.fetchall():
        try:
            st = datetime.fromisoformat(start_time)
            et = datetime.fromisoformat(end_time)
            total_seconds += int((et - st).total_seconds())
        except Exception:
            pass

    conn.close()
    return count or 0, first_seen, session_count or 0, first_session, int(total_seconds)


# ===========================================================
# АСИНХРОННЫЕ УТИЛИТЫ (пример)
# ===========================================================
async def get_user_by_nickname(nickname: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        async with db.execute("SELECT * FROM users WHERE nickname = ?", (nickname,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
