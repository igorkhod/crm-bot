# crm2/bot.py
"""
Модуль инициализации Telegram-бота.
Здесь создаётся экземпляр Bot и Dispatcher,
чтобы их можно было импортировать в других частях проекта.
"""

from aiogram import Bot, Dispatcher
import os

TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN/TELEGRAM_TOKEN не найден(ы) в окружении.")

# Инициализация
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()
