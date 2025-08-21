# === Файл: crm2/db/core.py
# Аннотация: единая точка подключения к SQLite; путь берёт из ENV DB_PATH или по умолчанию crm.db.

from __future__ import annotations
import os, sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parents[2] / "crm.db"))

def get_db_connection() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con
