# crm2/db/bootstrap.py
from __future__ import annotations
import sqlite3
from crm2.db.core import get_db_connection

def ensure_min_schema() -> None:
    """Ensure core tables exist on startup (idempotent)."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        # users
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER UNIQUE,
                username     TEXT,
                nickname     TEXT UNIQUE,
                password     TEXT,
                full_name    TEXT,
                role         TEXT DEFAULT 'user',
                phone        TEXT,
                email        TEXT,
                events       TEXT,
                participants TEXT,
                cohort_id    INTEGER
            )
            """
        )
        # cohorts
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cohorts (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        # participants
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER UNIQUE,
                cohort_id  INTEGER,
                stream_id  INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
