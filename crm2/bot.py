# crm2/bot.py
"""
Модуль инициализации Telegram-бота.
Здесь создаётся экземпляр Bot и Dispatcher,
чтобы их можно было импортировать в других частях проекта.
"""
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не найден в окружении.")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # ✅ правильный способ
)
dp = Dispatcher()
