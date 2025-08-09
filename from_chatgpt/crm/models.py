# import aiosqlite
from typing import Optional

import aiosqlite

from .db import DB_PATH


async def init_crm_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                nickname TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS streams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                title TEXT,
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stream_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(stream_id) REFERENCES streams(id)
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_id INTEGER,
                title TEXT,
                date TEXT,
                FOREIGN KEY(stream_id) REFERENCES streams(id)
            )
        ''')

        await conn.commit()


async def get_user_by_nickname(nickname: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
        row = await cursor.fetchone()
        if row:
            return dict(zip([column[0] for column in cursor.description], row))
        return None


async def create_user(telegram_id: int, nickname: str, password: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        await conn.execute(
            "INSERT INTO users (telegram_id, nickname, password) VALUES (?, ?, ?)",
            (telegram_id, nickname, password)
        )
        conn.commit()


async def update_user_password(nickname: str, new_password: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        await conn.execute(
            "UPDATE users SET password = ? WHERE nickname = ?",
            (new_password, nickname)
        )
        conn.commit()


async def update_admin_role(admin_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE users SET role = 'admin' WHERE telegram_id = ?",
            (admin_id,)
        )
        await conn.commit()


async def delete_user_password(telegram_id: int):
    conn = aiosqlite.connect(DB_PATH)
    cursor = conn.cursor()
    await conn.execute("UPDATE users SET password = NULL WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()


async def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = await cursor.fetchone()
        return dict(user) if user else None
