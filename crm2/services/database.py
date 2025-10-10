# crm2/services/database.py
import aiosqlite
import logging
import os
import pathlib
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def _resolve_db_path() -> str:
    """
    Порядок:
      1) DB_PATH из .env/.env.local
      2) CRM_DB из .env/.env.local
      3) локальный путь crm2/data/crm.db
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    candidates = [
        os.getenv("DB_PATH"),
        os.getenv("CRM_DB"),
        os.path.join(root, "data", "crm.db"),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return candidates[-1]

DB_PATH = _resolve_db_path()

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def execute(self, query: str, params: tuple = ()) -> None:
        """Выполняет запрос на изменение данных"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, params)
                await db.commit()
        except Exception as e:
            logger.error(f"Database execute error: {e}")
            raise

    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Выполняет запрос и возвращает все результаты"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Database fetch_all error: {e}")
            return []

    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Выполняет запрос и возвращает одну строку"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Database fetch_one error: {e}")
            return None

# Инициализация базы данных
db = Database(DB_PATH)