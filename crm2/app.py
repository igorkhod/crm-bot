# 📄 crm2/app.py
# app
# Назначение: главный вход бота (aiogram v3).
# Что делает:
# инициализирует логирование и конфигурацию (BOT_TOKEN, ADMIN_ID);
# подключает сессию Telegram API;
# регистрирует обработчики старта/остановки бота (с уведомлениями администратору);
# включает в диспетчер все основные роутеры: consent, start, registration, auth, info, help, about, profile, attendance;
# подключает админ-панель, DB Doctor и ChatGPT-роутер;
# запускает цикл polling.
# Расположение:
# crm2/
#  └── app.py
# === Автогенерированный заголовок: crm2/app.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: try_include, main
# === Конец автозаголовка
# === Файл: crm2/app.py
# Точка входа бота (aiogram v3). Инициализация, подключение роутеров, запуск.
from __future__ import annotations

import asyncio
import importlib
import logging
import markdown
import os
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# если у тебя уже есть FastAPI app, используй его!
web_app = FastAPI()

@web_app.get("/info/meanings", response_class=HTMLResponse)
async def get_meanings():
    path = Path(__file__).parent / "content" / "info" / "meanings.md"
    if not path.exists():
        return "<h1>Файл meanings.md не найден</h1>"
    md_text = path.read_text(encoding="utf-8")
    html = markdown.markdown(md_text, extensions=["extra", "nl2br", "sane_lists"])
    return f"""
    <html>
      <head>
        <meta charset="utf-8">
        <title>Смыслы проекта</title>
      </head>
      <body style="max-width:800px;margin:auto;font-family:sans-serif;line-height:1.6;">
        {html}
      </body>
    </html>
    """


# ────────────────────────────── ЛОГИ ──────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

# ───────────────────────────── КОНФИГ ─────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN/TELEGRAM_TOKEN не задан(ы) в окружении.")

# ─────────────────────────── РОУТЕРЫ (фикс) ───────────────────────
# Явные модули, которые точно есть
from crm2.handlers import consent
from crm2.handlers import start
from crm2.handlers import registration
from crm2.handlers import auth
from crm2.handlers import info
from crm2.handlers import help as help_router
from crm2.handlers import about as about_router
from crm2.handlers import profile as profile_router
from crm2.handlers import attendance as attendance_router
from crm2.handlers.admin import chatgpt as admin_chatgpt

# Админ: панель и DB Doctor (подключим раньше прочих админ-модулей)
from crm2.handlers.admin import panel as admin_panel_router
from crm2.handlers import admin_db_doctor as admin_db_doctor_router

# Вспомогательные миграции
from crm2.db.auto_migrate import ensure_schedule_schema


def try_include(dp: Dispatcher, module_path: str, attr: str = "router") -> None:
    """
    Безопасно подключает роутер из модуля, если модуль/атрибут есть.
    Нужен, чтобы Pycharm не ругался и запуск не падал при отсутствии файла.
    """
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        logging.info(f"[ROUTER:skip] {module_path} (module not found)")
        return

    router = getattr(mod, attr, None)
    if router is None:
        logging.info(f"[ROUTER:skip] {module_path}.{attr} not found")
        return

    dp.include_router(router)
    logging.info(f"[ROUTER:ok] {module_path}.{attr} included")


async def main() -> None:
    logging.warning("[BUILD] starting application")

    # Миграции/схемы (самолечащиеся)
    try:
        ensure_schedule_schema()
        logging.info("[SCHEMA] ensured")
    except Exception as e:
        logging.error(f"[SCHEMA] ensure_schedule_schema failed: {e}")

    # Сессия TG API — целочисленный таймаут (во избежание ClientTimeout+int)
    session = AiohttpSession(timeout=70)

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # --- 🔔 старт/стоп-уведомления администратору ---
    # Используем существующий ADMIN_ID (твои env уже содержат его).
    # Флаги можно не задавать: по умолчанию уведомления включены.
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
    NOTIFY_STARTUP = os.getenv("NOTIFY_STARTUP", "1") == "1"
    NOTIFY_SHUTDOWN = os.getenv("NOTIFY_SHUTDOWN", "1") == "1"

    async def _on_startup(bot: Bot):
        if NOTIFY_STARTUP and ADMIN_ID:
            try:
                await bot.send_message(ADMIN_ID, "🚀 Бот запущен!")
            except Exception as e:
                print(f"[notify] startup failed: {e}")

    async def _on_shutdown(bot: Bot):
        if NOTIFY_SHUTDOWN and ADMIN_ID:
            try:
                await bot.send_message(ADMIN_ID, "⛔ Бот остановлен.")
            except Exception as e:
                print(f"[notify] shutdown failed: {e}")

    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)
    # --- /🔔 ---

    # ───────────────────── ПОДКЛЮЧЕНИЕ РОУТЕРОВ ─────────────────────
    # 1) Узкие/системные
    dp.include_router(consent.router)
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(auth.router)

    # 2) Админ: панель и СРАЗУ DB Doctor (чтобы перехватывал свои кнопки первым)
    dp.include_router(admin_panel_router.router)
    dp.include_router(admin_db_doctor_router.router)

    # 3) Остальные админ-подсекции (могут отсутствовать — подключаем мягко)
    try_include(dp, "crm2.handlers.admin_users")  # если есть crm2/handlers/admin_users.py
    try_include(dp, "crm2.handlers.admin_schedule")  # если есть crm2/handlers/admin_schedule.py
    try_include(dp, "crm2.handlers.admin_logs")  # если есть crm2/handlers/admin_logs.py
    try_include(dp, "crm2.handlers.admin_broadcast")  # если есть crm2/handlers/admin_broadcast.py
    try_include(dp, "crm2.handlers.admin_db")  # команды /db_* (если модуль есть)

    # 4) Пользовательские разделы
    dp.include_router(info.router)
    dp.include_router(help_router.router)
    dp.include_router(about_router.router)
    dp.include_router(profile_router.router)
    dp.include_router(attendance_router.router)
    dp.include_router(admin_chatgpt.router)

    # Если где-то есть общий роутер расписания типа crm2/handlers_schedule.py с router,
    # можно мягко подключить и его:
    try_include(dp, "crm2.handlers_schedule")  # подключится только если есть attr "router"

    # ───────────────────────────── ЗАПУСК ───────────────────────────
    # if ADMIN_ID:
    #     try:
    #         await bot.send_message(int(ADMIN_ID), "🚀 Бот запущен!")
    #     except Exception as e:
    #         logging.warning(f"ADMIN notify failed: {e}")

    try:
        await dp.start_polling(
            bot,
            polling_timeout=60,
            allowed_updates=None,
            drop_pending_updates=False,
        )
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt — завершаем…")
    finally:
        await bot.session.close()
        logging.info("Сессия закрыта.")


if __name__ == "__main__":
    asyncio.run(main())
