# crm2/config.py — аккуратное чтение окружения (без dataclasses), совместимость со старым кодом
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# === 1) Пути проекта ===
CRM2_DIR: Path = Path(__file__).resolve().parent          # .../crm2
PROJ_ROOT: Path = CRM2_DIR.parent                         # .../ (корень проекта)

# === 2) Загружаем .env (локальная отладка приоритетнее) ===
for env_name in (".env.local", ".env.prod", ".env"):
    env_path = PROJ_ROOT / env_name
    if env_path.exists():
        load_dotenv(env_path, override=False)  # уважаем уже выставленные переменные

# === 3) Утилиты преобразования типов ===
def _to_bool(x: str | None, default: bool = False) -> bool:
    if x is None:
        return default
    return x.strip().lower() in {"1", "true", "yes", "y", "on"}

def _to_int(x: str | None, default: int) -> int:
    try:
        return int(x) if x is not None else default
    except ValueError:
        return default

# === 4) Базовые настройки ===
ENV: str = os.getenv("ENV", "production")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").split("#", 1)[0].strip()
DEBUG: bool = _to_bool(os.getenv("DEBUG"), default=False)
TZ: str = os.getenv("TZ", "Europe/Helsinki")

# Токены и ключи
BOT_TOKEN: str | None = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
ADMIN_ID: str | None = os.getenv("ADMIN_ID")

# Сетевые параметры (на случай вебхуков/веб-сервера)
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = _to_int(os.getenv("PORT"), 8080)

HTTP_TIMEOUT: int = _to_int(os.getenv("HTTP_TIMEOUT"), 20)
RETRY_COUNT: int = _to_int(os.getenv("RETRY_COUNT"), 3)

# === 5) Пути к данным/БД ===
_default_data_dir = Path("/var/data")
DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(_default_data_dir if _default_data_dir.exists() else CRM2_DIR / "data"))).resolve()

_db_env = os.getenv("CRM_DB_PATH") or os.getenv("DB_PATH")
if _db_env:
    DB_PATH: str = _db_env
else:
    default_candidates = [
        DATA_DIR / "crm.db",
        CRM2_DIR / "data" / "crm.db",
    ]
    DB_PATH = str(next((p for p in default_candidates if p), default_candidates[-1]))

# === 6) Совместимость со старым интерфейсом get_settings() ===
def get_settings():
    """
    Унифицированные настройки проекта для старого кода (без dataclass).

    Приоритет DB_PATH:
      1) переменные окружения CRM_DB_PATH / DB_PATH,
      2) DATA_DIR/crm.db (где DATA_DIR = /var/data при наличии),
      3) локальный файл crm2/data/crm.db.
    """
    db = os.getenv("CRM_DB_PATH") or os.getenv("DB_PATH")
    if not db:
        data_dir = Path(os.getenv("DATA_DIR", str(DATA_DIR)))
        candidate = data_dir / "crm.db"
        if not candidate.exists():
            candidate = CRM2_DIR / "data" / "crm.db"
        db = str(candidate)
    level = os.getenv("LOG_LEVEL", LOG_LEVEL)
    return {"DB_PATH": db, "LOG_LEVEL": level}

__all__ = [
    # Пути
    "CRM2_DIR", "PROJ_ROOT", "DATA_DIR", "DB_PATH",
    # Режимы
    "ENV", "LOG_LEVEL", "DEBUG", "TZ",
    # Ключи/сеть
    "BOT_TOKEN", "OPENAI_API_KEY", "ADMIN_ID",
    "HOST", "PORT", "HTTP_TIMEOUT", "RETRY_COUNT",
    # Совместимость
    "get_settings",
]

if __name__ == "__main__":
    s = get_settings()
    print("DB_PATH:", DB_PATH)
    print("ENV:", ENV, "LOG_LEVEL:", LOG_LEVEL, "DEBUG:", DEBUG, "TZ:", TZ)
    print("get_settings():", s)
