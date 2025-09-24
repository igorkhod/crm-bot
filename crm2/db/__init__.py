# crm2/db/__init__.py
# Экспортируем db. Здесь же создаём простой «асинхронный» адаптер
# над sqlite3 на основе твоей функции get_db_connection() из core.py.

from __future__ import annotations

from .core import get_db_connection
from .sessions import get_upcoming_sessions, get_session_by_id

# Простой адаптер под await-API, поверх синхронного sqlite3.
# Если позже перейдёшь на aiosqlite — реализация методов останется той же.
class Database:
    def __init__(self):
        self._get_connection = get_db_connection

    async def execute(self, sql: str, params: tuple = ()) -> None:
        con = self._get_connection()
        try:
            cur = con.cursor()
            cur.execute(sql, params)
            con.commit()
        finally:
            con.close()

    async def fetch_all(self, sql: str, params: tuple = ()):
        con = self._get_connection()
        try:
            cur = con.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows
        finally:
            con.close()

    async def fetch_one(self, sql: str, params: tuple = ()):
        con = self._get_connection()
        try:
            cur = con.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            return row
        finally:
            con.close()

# ✅ Экспортируемый во всём проекте объект БД
db = Database()

__all__ = [
    "db",
    "get_upcoming_sessions",
    "get_session_by_id",
]
