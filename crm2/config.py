# === Автогенерированный заголовок: crm2/config.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: Settings, _Settings
# Функции: get_settings
# === Конец автозаголовка
#
# === Файл: crm2/config.py
# Аннотация: модуль CRM, настройки/конфигурация, загрузка конфигурации из .env
# crm2/config.py
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass

# 1) Грузим .env.* (локальная отладка приоритетнее)
cwd = Path(__file__).resolve().parents[1]  # .../crm2
proj_root = cwd.parent                     # .../ (корень проекта)

for env_name in (".env.local", ".env.prod", ".env"):
    env_path = proj_root / env_name
    if env_path.exists():
        load_dotenv(env_path, override=False)

# 2) Путь к БД
#    Можно переопределить переменной окружения DB_PATH
default_db = proj_root / "crm2" / "data" / "crm.db"
DB_PATH = os.getenv("DB_PATH", str(default_db))

# 3) Прочие базовые настройки (по желанию)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").split("#", 1)[0]
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


# --- shim для совместимости: get_settings() ---
@dataclass(frozen=True)
class _Settings:
    DB_PATH: str
    LOG_LEVEL: str = "INFO"

def get_settings() -> _Settings:
    """
    Унифицированные настройки проекта.

    Приоритет DB_PATH:
    1) переменная окружения CRM_DB_PATH,
    2) локальный файл crm2/data/crm.db (по умолчанию для разработки).
    """
    env_db = os.getenv("DB_PATH")
    if env_db:
        db_path = env_db
    else:
        crm2_dir = Path(__file__).resolve().parent
        db_path = str(crm2_dir / "data" / "crm.db")

    log_level = os.getenv("LOG_LEVEL", "INFO")
    return _Settings(DB_PATH=db_path, LOG_LEVEL=log_level)