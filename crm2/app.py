from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import pathlib
import sqlite3
from contextlib import suppress

# === Автогенерированный заголовок: crm2/app.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: _load_env, _try_include, _test_db, _runner, main, health, _on_startup, _on_shutdown
# === Конец автозаголовка
# crm2/app.py
# ... остальной код без изменений ...

from dotenv import load_dotenv
from fastapi import FastAPI

from crm2.middlewares.callback_auth_middleware import CallbackAuthMiddleware


# ----------------- ENV -----------------
def _load_env():
    """
    Приоритет:
    1) Если задан ENV_FILE и файл существует — грузим его.
    2) Иначе ищем рядом с корнем проекта: .env.local -> .env -> .env.prod.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    env_file = os.getenv("ENV_FILE")
    if env_file and pathlib.Path(env_file).exists():
        load_dotenv(env_file, override=False)
        return
    for cand in (".env.local", ".env", ".env.prod"):
        p = root / cand
        if p.exists():
            load_dotenv(p, override=False)
            return


# Загружаем окружение до импорта бота
_load_env()

# Для отладки печатаем первые символы токена
key = "TELEGRAM_TOKEN"
val = os.getenv(key)
if val:
    print(f"{key} = {val[:5]}*****")
else:
    print(f"{key} = <не найден>")

from crm2.bot import bot, dp  # теперь окружение уже прогружено
from crm2.middlewares.auth_middleware import AuthMiddleware

# ----------------- FASTAPI -----------------
app = FastAPI(title="crm2")


@app.get("/health")
async def health():
    return {"ok": True}


# ...после импорта bot, dp и загрузки .env:
ADMIN_ID = os.getenv("ADMIN_ID")
try:
    ADMIN_ID = int(ADMIN_ID) if ADMIN_ID else None
except ValueError:
    ADMIN_ID = None
    logging.warning("ADMIN_ID в .env некорректный (не число) — оповещение в Telegram отключено.")


# ----------------- ROUTERS -----------------
def _try_include(module_path: str, attr: str = "router"):
    """Пытаемся подключить роутер модуля, пишем в лог результат."""
    try:
        mod = __import__(module_path, fromlist=[attr])
        r = getattr(mod, attr)
        dp.include_router(r)
        logging.getLogger().info("[ROUTER:ok] %s.%s included", module_path, attr)
    except ModuleNotFoundError:
        logging.getLogger().info("[ROUTER:skip] %s (module not found)", module_path)
    except Exception as e:
        logging.getLogger().exception("[ROUTER:fail] %s: %s", module_path, e)


# добавь ниже функции _try_include(...) вот эти два коллбека
async def _on_startup():
    if ADMIN_ID:
        with contextlib.suppress(Exception):
            await bot.send_message(ADMIN_ID, "🚀 Бот запущен и готов к работе!")


async def _on_shutdown():
    if ADMIN_ID:
        with contextlib.suppress(Exception):
            await bot.send_message(ADMIN_ID, "⛔️ Бот остановлен.")


# ----------------- DB TEST -----------------
def _test_db():
    """Пробуем открыть crm.db и выполнить SELECT 1."""
    db_path = pathlib.Path(__file__).resolve().parent / "data" / "crm.db"
    if not db_path.exists():
        logging.warning(f"[DB] Файл базы {db_path} не найден")
        return
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT 1")
        res = cur.fetchone()
        logging.info(f"[DB] Подключение успешно, SELECT 1 -> {res}")
        con.close()
    except Exception as e:
        logging.exception(f"[DB] Ошибка при подключении: {e}")


# ----------------- RUNNER -----------------
async def _runner():
    # проверка базы перед стартом
    _test_db()

    # Регистрируем middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(CallbackAuthMiddleware())

    # ---- Основные хендлеры ----
    _try_include("crm2.handlers.start")
    _try_include("crm2.handlers.welcome")
    _try_include("crm2.handlers.auth")
    _try_include("crm2.handlers.registration")
    _try_include("crm2.handlers.consent")
    _try_include("crm2.handlers.main_menu")
    _try_include("crm2.handlers.guest_menu")
    _try_include("crm2.handlers.profile")
    _try_include("crm2.handlers.stream_selfset")

    # ---- Информационные хендлеры ----
    _try_include("crm2.handlers.about")
    _try_include("crm2.handlers.help")
    _try_include("crm2.handlers.info")  # включает расписание

    # ---- Админские хендлеры ----
    _try_include("crm2.handlers.admin.panel")
    _try_include("crm2.handlers.admin.attendance")
    _try_include("crm2.handlers.admin.admin_homework")  # полная версия
    _try_include("crm2.handlers.admin.users")
    _try_include("crm2.handlers.admin.schedule")
    _try_include("crm2.handlers.admin.broadcast")
    _try_include("crm2.handlers.admin.chatgpt")
    _try_include("crm2.handlers.admin.logs")
    _try_include("crm2.handlers.admin.db")

    # ---- Дополнительные админские модули ----
    _try_include("crm2.handlers.admin_db")
    _try_include("crm2.handlers.admin_db_doctor")
    _try_include("crm2.handlers.admin_users")

    # Регистрируем startup/shutdown
    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)

    logging.warning("[BUILD] starting application")

    try:
        logging.info("🚀 Бот запущен и готов к работе!")
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception("❌ Ошибка в работе бота: %s", e)
    finally:
        await bot.session.close()
        logging.info("⛔️ Бот остановлен.")


# ----------------- MAIN -----------------
def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    with suppress(KeyboardInterrupt):
        asyncio.run(_runner())


if __name__ == "__main__":
    main()