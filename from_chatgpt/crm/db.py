import aiosqlite
import sqlite3  # нужен только для RowFactory
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "crm.db"


def init_db():
    """Создаёт таблицы и добавляет недостающие столбцы"""
    conn = aiosqlite.connect(DB_PATH)
    cur = conn.cursor()

    # Таблица пользователей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT,
            first_seen TEXT
        )
    """)

    # Таблица сессий
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (user_id) REFERENCES visitors (user_id)
        )
    """)

    # Проверим, что в таблице sessions есть колонка end_time
    cur.execute("PRAGMA table_info(sessions)")
    columns = [row[1] for row in cur.fetchall()]
    if "end_time" not in columns:
        cur.execute("ALTER TABLE sessions ADD COLUMN end_time TEXT")

    conn.commit()
    conn.close()


def update_visitor(user_id: int, nickname: str):
    """Добавляет нового пользователя или обновляет его имя"""
    conn = aiosqlite.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM visitors WHERE user_id=?", (user_id,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO visitors (user_id, nickname, first_seen) VALUES (?, ?, ?)",
            (user_id, nickname, datetime.utcnow().isoformat()),
        )
    else:
        cur.execute(
            "UPDATE visitors SET nickname=? WHERE user_id=?",
            (nickname, user_id),
        )

    conn.commit()
    conn.close()


def start_session(user_id: int):
    """Открывает новую сессию"""
    conn = aiosqlite.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO sessions (user_id, start_time) VALUES (?, ?)",
        (user_id, datetime.utcnow().isoformat()),
    )

    conn.commit()
    conn.close()


def update_session(user_id: int):
    """Обновляет время последней сессии (end_time)"""
    conn = aiosqlite.connect(DB_PATH)
    cur = conn.cursor()

    # Найдём последнюю сессию этого пользователя
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
    conn = aiosqlite.connect(DB_PATH)
    cur = conn.cursor()

    # Кол-во пользователей и первый визит
    cur.execute("SELECT COUNT(*), MIN(first_seen) FROM visitors")
    count, first_seen = cur.fetchone()

    # Кол-во сессий и первая сессия
    cur.execute("SELECT COUNT(*), MIN(start_time) FROM sessions")
    session_count, first_session = cur.fetchone()

    # Суммарное время по всем сессиям
    cur.execute("""
        SELECT start_time, end_time FROM sessions WHERE end_time IS NOT NULL
    """)
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