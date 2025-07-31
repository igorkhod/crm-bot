import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
# from aiogram.utils import executor
import aiogram.utils.executor as executor
from dotenv import load_dotenv

# 🌿 Загружаем переменные из token.env
load_dotenv(dotenv_path="token.env")
API_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🔧 Проверка: токен должен быть найден
if not API_TOKEN:
    raise ValueError("Токен не найден. Проверь файл token.env и ключ TELEGRAM_TOKEN.")

# 🤖 Создаем бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 🧙 Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: Message):
    await message.answer("Привет, путник! Это начало твоего пути с Python.")

# 🌞 Команда /hello
@dp.message_handler(commands=["hello"])
async def hello_command(message: Message):
    await message.answer("Приветствую тебя, странник!")

# 🎲 Команда /random
@dp.message_handler(commands=["random"])
async def random_command(message: Message):
    import random
    number = random.randint(1, 100)
    await message.answer(f"Случайное число: {number}")

# 🔄 Ответ на всё остальное
@dp.message_handler()
async def echo_handler(message: Message):
    await message.answer(f"Ты сказал: {message.text}")

# 🚀 Запуск
if __name__ == "__main__":
    print("Бот запущен. Ожидает команд в Telegram...")
    executor.start_polling(dp, skip_updates=True)
