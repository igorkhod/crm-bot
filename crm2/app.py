from __future__ import annotations  # ← ДОЛЖНО быть первым (после докстринга/комментариев)

import logging
import os
import sqlite3  # ← добавили

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from dotenv import load_dotenv

from crm2.db.sqlite import DB_PATH  # ← добавили
from crm2.db.sqlite import ensure_schema
from crm2.handlers import auth  # <— новое
from crm2.handlers import registration
from crm2.keyboards import guest_start_kb, role_kb
from crm2.routers import start
from crm2.handlers import info  # ← импорт


def _get_role_from_db(tg_id: int) -> str:
    """Без автоклассификации: читаем роль из БД как есть."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE telegram_id = ?", (tg_id,))
        row = cur.fetchone()
        return (row["role"] if row and row["role"] else "curious")


load_dotenv()

ensure_schema()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(registration.router)
dp.include_router(auth.router)  # <— новое
dp.include_router(info.router)  # ← подключение


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    # НИЧЕГО НЕ ЧИТАЕМ И НЕ ПИШЕМ В БД!
    await message.answer(
        "Добро пожаловать в CRM2!\nВы гость. Выберите действие:",
        reply_markup=guest_start_kb(),
    )


@dp.message(F.text.in_({"/home", "Мой кабинет"}))
async def cmd_home(message: Message):
    role = _get_role_from_db(message.from_user.id)  # только чтение
    if role in (None, "", "curious"):
        await message.answer(
            "Вы ещё не авторизованы. Войдите или зарегистрируйтесь:",
            reply_markup=guest_start_kb(),
        )
    else:
        await message.answer(
            f"Ваш кабинет. Роль: {role}",
            reply_markup=role_kb(role),
        )



async def main() -> None:
    # мягкий запуск: сообщаем админу (если указан)
    if ADMIN_ID:
        try:
            await bot.send_message(int(ADMIN_ID), "🚀 Бот запущен и готов к работе!")
        except Exception as e:
            logging.error(f"Не удалось написать админу при старте: {e}")

    try:
        # просто стартуем поллинг; на Windows без сигналов
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Получен KeyboardInterrupt — завершаем...")
    finally:
        # уведомление админу и корректное закрытие сессии при любом исходе
        if ADMIN_ID:
            try:
                await bot.send_message(int(ADMIN_ID), "⛔ Бот остановлен.")
            except Exception as e:
                logging.error(f"Не удалось написать админу при остановке: {e}")
        await bot.session.close()
        logging.info("Сессия закрыта.")
