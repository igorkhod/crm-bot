import asyncio
import logging
import os
from pathlib import Path

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from dotenv import load_dotenv

from crm.handlers_admin_info import register_admin_info_handlers
from from_chatgpt.crm.models import init_crm_db, update_admin_role
from crm.handlers_registration_login_reset_email import registration_router
from from_chatgpt.crm.db import DB_PATH, init_db

# Загрузка переменных окружения
dotenv_path = Path(__file__).resolve().parent / "token_local.env"
load_dotenv(dotenv_path)

TOKEN = os.getenv("TELEGRAM_TOKEN")
# ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_ID = os.getenv("ADMIN_ID")
print(f"📥 TOKEN:  {TOKEN[:5]}..., обрезано безопасностью")
print(f"Загруженный ADMIN_ID из .env: {str(ADMIN_ID)[:5]}..., обрезано безопасностью")


# Вывод информации о БД
async def inspect_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = await cursor.fetchall()
        print(f"📂 CRM база подключена. Найдено таблиц: {len(tables)}")
        for t in tables:
            print(f"🔹 Таблица: {t[0]}")


print(f"База данных: {DB_PATH}")


# Инициализация и запуск бота
async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    await inspect_db()
    await init_crm_db()
    await inspect_db()
    print("📦 Инициализация CRM-базы...")
    await update_admin_role(ADMIN_ID)
    print("🛠 Обновление роли администратора...")

    # bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    from crm.handlers_info_schedule import info_schedule_router
    from crm.handlers_admin_schedule import admin_schedule_router
    dp.include_router(info_schedule_router)
    dp.include_router(admin_schedule_router)

    # регистрация_роутеров
    dp.include_router(registration_router)
    # Регистрируем хендлеры админ-панели и информации
    register_admin_info_handlers(dp)

    print("🤖 Регистрация хендлеров...")
    print("🚀 Бот запущен. Ожидание событий...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
