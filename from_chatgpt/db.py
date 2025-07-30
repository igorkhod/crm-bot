import sqlite3
from datetime import datetime

DB_FILE = "bot_data.sqlite3"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        # таблица пользователей
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TEXT
        )
        """)
        # таблица сессий
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TEXT,
            last_active TEXT
        )
        """)
        conn.commit()

def update_visitor(user_id: int, username: str):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if cur.fetchone():
            return
        cur.execute(
            "INSERT INTO users (user_id, username, first_seen) VALUES (?, ?, ?)",
            (user_id, username, now),
        )
        conn.commit()

def start_session(user_id: int):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions (user_id, start_time, last_active) VALUES (?, ?, ?)",
            (user_id, now, now),
        )
        conn.commit()

def update_session(user_id: int):
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE sessions SET last_active=? WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (now, user_id),
        )
        conn.commit()

def get_stats():
    with get_connection() as conn:
        cur = conn.cursor()
        # кол-во пользователей и первый визит
        cur.execute("SELECT COUNT(*), MIN(first_seen) FROM users")
        user_count, first_seen = cur.fetchone()
        # кол-во сеансов
        cur.execute("SELECT COUNT(*), MIN(start_time) FROM sessions")
        session_count, first_session = cur.fetchone()
        # суммарное время (по всем сессиям)
        cur.execute("SELECT start_time, last_active FROM sessions")
        total_seconds = 0
        for start, last in cur.fetchall():
            if start and last:
                t1 = datetime.fromisoformat(start)
                t2 = datetime.fromisoformat(last)
                total_seconds += int((t2 - t1).total_seconds())
        return user_count or 0, first_seen, session_count or 0, first_session, total_seconds
