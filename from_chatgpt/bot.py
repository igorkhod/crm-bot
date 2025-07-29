import asyncio
import os
import random
import json
from datetime import datetime
from pathlib import Path
import threading
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from pytils.dt import ru_strftime
from dotenv import load_dotenv

load_dotenv("/etc/secrets/token.env")

# Загружаем токены
# load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Путь к цитатам
QUOTES_FILE = Path(__file__).parent / "data" / "quotes.json"

# Города
CITIES = {
    "Красноярск": "Krasnoyarsk",
    "Иркутск": "Irkutsk"
}

WEEKDAYS_RU = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}


def main_keyboard():
    kb = [
        [KeyboardButton(text="🔮 Психонетика Инь-Ян"),
         KeyboardButton(text="🌲 Иркутск психотехнологии")],
        [KeyboardButton(text="📅 Календарь"),
         KeyboardButton(text="🌤 Погода")],
        [KeyboardButton(text="💵 Курс валют"),
         KeyboardButton(text="💬 Цитата")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def city_keyboard():
    kb = [
        [KeyboardButton(text="Красноярск"),
         KeyboardButton(text="Иркутск")],
        [KeyboardButton(text="↩️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def load_quotes():
    if QUOTES_FILE.exists():
        try:
            with open(QUOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


# --- Команды ---
# @dp.message(Command("start"))
# async def cmd_start(message: Message):
#     today = datetime.now()
#     weekday = WEEKDAYS_RU.get(today.strftime("%A"), today.strftime("%A"))
#     date_str = today.strftime("%d.%m.%Y") + f" ({weekday})"
#     await message.answer(f"Добро пожаловать!\nСегодня {date_str}\nВыберите действие:",
#                          reply_markup=main_keyboard())
@dp.message(Command("start"))
async def cmd_start(message: Message):
    today = datetime.now()
    weekday = WEEKDAYS_RU.get(today.strftime("%A"), today.strftime("%A"))
    date_str = today.strftime("%d.%m.%Y") + f" ({weekday})"

    # Добавим метку сервиса
    host = os.environ.get("RENDER_SERVICE_NAME", "LOCAL")

    await message.answer(
        f"Добро пожаловать!\nСегодня {date_str}\n"
        f"Ответ сервера: {host}",
        reply_markup=main_keyboard()
    )


@dp.message(Command("time"))
async def cmd_time(message: Message):
    now = datetime.now().strftime("%H:%M:%S")
    await message.answer(f"Сейчас {now}")


# --- Обработка кнопок ---
@dp.message(lambda m: m.text == "🔮 Психонетика Инь-Ян")
async def link_psychonetics(message: Message):
    await message.answer("🔗 https://t.me/+EL9esd0xZ-xkMTU6", reply_markup=main_keyboard())


@dp.message(lambda m: m.text == "🌲 Иркутск психотехнологии")
async def link_irkutsk(message: Message):
    await message.answer("🔗 https://t.me/+7ZBrobhAJoRhM2U6", reply_markup=main_keyboard())


@dp.message(lambda m: m.text == "📅 Календарь")
async def show_calendar(message: Message):
    calendar, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').build()
    await message.answer("Выберите год", reply_markup=calendar)


@dp.callback_query(DetailedTelegramCalendar.func(calendar_id=1))
async def process_calendar(callback_query: types.CallbackQuery):
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').process(callback_query.data)
    if not result and key:
        await callback_query.message.edit_text(f"Выберите {LSTEP[step]}", reply_markup=key)
    elif result:
        await callback_query.message.edit_text(f"Вы выбрали {result}")
        await callback_query.message.answer("Что дальше?", reply_markup=main_keyboard())


@dp.message(lambda m: m.text == "🌤 Погода")
async def ask_city(message: Message):
    await message.answer("Выберите город:", reply_markup=city_keyboard())


@dp.message(lambda m: m.text in CITIES)
async def weather(message: Message):
    city = message.text
    code = CITIES[city]
    url = f"http://api.openweathermap.org/data/2.5/weather?q={code},RU&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        r = requests.get(url)
        data = r.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description'].capitalize()
        await message.answer(f"Погода в {city}: {temp:.1f}°C, {desc}", reply_markup=main_keyboard())
    except Exception as e:
        await message.answer(f"Ошибка получения погоды: {e}", reply_markup=main_keyboard())


@dp.message(lambda m: m.text == "💵 Курс валют")
async def currency(message: Message):
    data = requests.get("https://www.cbr-xml-daily.ru/daily_json.js").json()
    usd = data['Valute']['USD']['Value']
    eur = data['Valute']['EUR']['Value']
    await message.answer(f"USD: {usd:.2f}₽\nEUR: {eur:.2f}₽", reply_markup=main_keyboard())


@dp.message(lambda m: m.text == "💬 Цитата")
async def quote(message: Message):
    quotes = load_quotes()
    if not quotes:
        await message.answer("Нет цитат.", reply_markup=main_keyboard())
        return
    q = random.choice(quotes)
    text = q['text'] if isinstance(q, dict) else str(q)
    await message.answer(f"«{text}»", reply_markup=main_keyboard())


@dp.message(lambda m: m.text == "❓ Помощь")
async def help_cmd(message: Message):
    await message.answer("Помощь: календарь, погода, курс валют, цитаты.", reply_markup=main_keyboard())


@dp.message(lambda m: m.text == "↩️ Назад")
async def back(message: Message):
    await message.answer("Главное меню:", reply_markup=main_keyboard())


# --- Мини веб-сервер, чтобы Render не засыпал ---
app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok", "bot": "running"}


def run_web():
    uvicorn.run(app, host="0.0.0.0", port=10000)


async def main():
    threading.Thread(target=run_web, daemon=True).start()
    await dp.start_polling(bot)

async def call_chatgpt_api(prompt: str) -> str:
    api_key = os.getenv("IGOR_OPENAI_API")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            r = await resp.json()
            return r["choices"][0]["message"]["content"]

async def call_deepseek_api(prompt: str) -> str:
    api_key = os.getenv("IGOR_KHOD_DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            r = await resp.json()
            return r["choices"][0]["message"]["content"]

if __name__ == "__main__":
    asyncio.run(main())
