# === Автогенерированный заголовок: crm2/config.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: Settings
# Функции: get_settings
# === Конец автозаголовка
#
# === Файл: crm2/config.py
# Аннотация: модуль CRM, настройки/конфигурация, загрузка конфигурации из .env. Внутри классы: Settings, функции: get_settings.
# Добавлено автоматически 2025-08-21 05:43:17

# crm2/config.py
# from __future__ import annotations
# import os
# from typing import Final
# from dataclasses import dataclass
# from pathlib import Path
#
# try:
#     from dotenv import load_dotenv  # локально не помешает, на сервере можно игнорировать
#     load_dotenv(Path(__file__).resolve().parents[1] / ".env")
# except Exception:
#     pass
#
# BASE_DIR = Path(__file__).resolve().parents[1]  # .../crm
#
# # На сервере Render есть /var/data → по умолчанию используем его.
# DEFAULT_DB: Final[str] = "/var/data/crm.db" if os.path.isdir("/var/data") else str(BASE_DIR / "crm2.db")
# DB_PATH: Final[str] = os.getenv("CRM_DB") or DEFAULT_DB
#
# # Глобальная точка правды для путя к БД (нужна модулям, которые делают `from crm2.config import DB_PATH`)
#
#
# @ dataclass(frozen=True)
# class Settings:
#     TELEGRAM_TOKEN: str
#     ADMIN_ID: int | None
#     LOG_LEVEL: str
#     DB_PATH: str
#
#
# def get_settings() -> Settings:
#     token = os.getenv("TELEGRAM_TOKEN")
#     if not token:
#         raise SystemExit("TELEGRAM_TOKEN не задан.")
#     admin_raw = (os.getenv("ADMIN_ID") or "").strip()
#     admin_id = int(admin_raw) if admin_raw.isdigit() else None
#     log_level = (os.getenv("LOG_LEVEL") or "INFO").upper()
#     # используем глобальную константу DB_PATH
#     return Settings(
#         TELEGRAM_TOKEN=token,
#         ADMIN_ID=admin_id,
#         LOG_LEVEL=log_level,
#         DB_PATH=DB_PATH,
#     )
#
# __all__ = ["get_settings", "Settings", "DB_PATH", "DEFAULT_DB", "BASE_DIR"]

# crm2/config.py
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# 1) Грузим .env.* (локальная отладка приоритетнее)
cwd = Path(__file__).resolve().parents[1]  # .../crm2
proj_root = cwd.parent                     # .../ (корень проекта)

for env_name in (".env.local", ".env.prod", ".env"):
    env_path = proj_root / env_name
    if env_path.exists():
        load_dotenv(env_path, override=False)

# 2) Путь к БД
#    Можно переопределить переменной окружения CRM_DB_PATH
default_db = proj_root / "crm2" / "data" / "crm.db"
DB_PATH = os.getenv("CRM_DB_PATH", str(default_db))

# 3) Прочие базовые настройки (по желанию)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").split("#", 1)[0]
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


# --- shim для совместимости: get_settings() ---
try:
    get_settings  # уже определена? тогда ничего не делаем
except NameError:
    from dataclasses import dataclass
    import os
    from pathlib import Path

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
        env_db = os.getenv("CRM_DB_PATH")
        if env_db:
            db_path = env_db
        else:
            crm2_dir = Path(__file__).resolve().parent
            db_path = str(crm2_dir / "data" / "crm.db")

        log_level = os.getenv("LOG_LEVEL", "INFO")
        return _Settings(DB_PATH=db_path, LOG_LEVEL=log_level)
