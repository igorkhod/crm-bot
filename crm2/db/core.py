# crm2/db/core.py
# Назначение: Предоставляет функцию для подключения к SQLite базе данных (единая точка входа)
# Функции:
# - get_db_connection - Возвращает соединение с базой данных (с row_factory = sqlite3.Row)

from __future__ import annotations
import sqlite3
from crm2.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con