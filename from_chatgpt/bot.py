from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os

from dotenv import load_dotenv
load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я живу в облаке 🕊️")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
