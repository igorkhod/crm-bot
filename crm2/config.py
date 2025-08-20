from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

# читаем переменные из ProjectCRM/.env (если есть python-dotenv — PyCharm сам подхватит через EnvFile;
# но и без него можно задать переменные в конфигурации запуска)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

@dataclass(frozen=True)
class Settings:
    TELEGRAM_TOKEN: str
    ADMIN_ID: int | None
    LOG_LEVEL: str
    DB_PATH: str

def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_TOKEN не задан (положите его в ProjectCRM/.env).")
    admin = os.getenv("ADMIN_ID")
    admin_id = int(admin) if (admin and admin.isdigit()) else None
    log_level = (os.getenv("LOG_LEVEL") or "INFO").upper()
    db_path = os.getenv("CRM_DB") or str(Path(__file__).resolve().parents[1] / "crm2.db")
    return Settings(token, admin_id, log_level, db_path)

