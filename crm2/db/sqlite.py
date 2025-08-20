from __future__ import annotations
import sqlite3
from pathlib import Path

# единая точка пути БД (лежит в корне проекта)
DB_PATH = str(Path(__file__).resolve().parents[2] / "crm2.db")

import sqlite3
from pathlib import Path

# DB_PATH = Path(... )  # у тебя уже задан
# ensure_schema()       # у тебя уже есть

def get_db_connection() -> sqlite3.Connection:
    """Единая точка подключения к SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # таблицы
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cohorts (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT UNIQUE,
            starts_at TEXT,
            ends_at   TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id   INTEGER UNIQUE,
            full_name     TEXT,
            nickname      TEXT UNIQUE,
            password_hash TEXT,
            role          TEXT CHECK(role IN ('curious','user','advanced_user','admin')) DEFAULT 'curious',
            cohort_id     INTEGER,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            last_seen     TEXT,
            FOREIGN KEY (cohort_id) REFERENCES cohorts(id) ON DELETE SET NULL
        )""")
        # мягкие ALTER (на случай, если колонка вдруг отсутствует)
        for ddl in [
            "ALTER TABLE users ADD COLUMN last_seen TEXT",
        ]:
            try:
                cur.execute(ddl)
            except sqlite3.OperationalError:
                pass
        conn.commit()
