# === Автогенерированный заголовок: crm2/db/core.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: get_db_connection
# === Конец автозаголовка
# crm2/db/core.py
# Аннотация: единая точка подключения к SQLite, использует DB_PATH из config.py

from __future__ import annotations
import sqlite3
from crm2.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con