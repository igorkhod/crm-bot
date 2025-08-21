#
# === Файл: crm2/config.py
# Аннотация: модуль CRM, настройки/конфигурация, загрузка конфигурации из .env. Внутри классы: Settings, функции: get_settings.
# Добавлено автоматически 2025-08-21 05:43:17

# crm2/config.py
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv  # локально не помешает, на сервере можно игнорировать
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]  # .../crm

# На сервере Render есть /var/data → по умолчанию используем его.
DEFAULT_DB = "/var/data/crm.db" if os.path.isdir("/var/data") else str(BASE_DIR / "crm2.db")

@dataclass(frozen=True)
class Settings:
    TELEGRAM_TOKEN: str
    ADMIN_ID: int | None
    LOG_LEVEL: str
    DB_PATH: str

def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_TOKEN не задан.")
    admin_raw = (os.getenv("ADMIN_ID") or "").strip()
    admin_id = int(admin_raw) if admin_raw.isdigit() else None
    log_level = (os.getenv("LOG_LEVEL") or "INFO").upper()
    db_path = os.getenv("CRM_DB") or DEFAULT_DB
    return Settings(token, admin_id, log_level, db_path)