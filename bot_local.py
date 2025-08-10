import os
import json
import random
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
import uvicorn
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import requests
import aiohttp
from db import init_db
from contextlib import asynccontextmanager

# ---- Определяем окружение и загружаем переменные ----
local_env = Path(__file__).parent / "token.env"

if local_env.exists():
    ENVIRONMENT = "LOCAL"
    load_dotenv(local_env)
    print("✅ Загружены переменные из локального token.env")
else:
    ENVIRONMENT = "RENDER"
    load_dotenv("/etc/secrets/token.env")
    print("✅ Загружены переменные из /etc/secrets/token.env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

bot = Bot(token=TOKEN)
init_db()
dp = Dispatcher()
app = FastAPI()

user_choice = {}
QUOTES_FILE = Path(__file__).parent / "data" / "quotes.json"

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


# === Основная клавиатура ===
def main_keyboard():
    kb = [
        [KeyboardButton(text="🔮 Психонетика Инь-Ян"),
         KeyboardButton(text="🌲 Иркутск психотехнологии")],
        [KeyboardButton(text="🌤 Погода"),
         KeyboardButton(text="💵 Курс валют")],
        [KeyboardButton(text="💬 Цитата"),
         KeyboardButton(text="🤖 Выбор ИИ")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def ai_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 ChatGPT", callback_data="ask_gpt"),
            InlineKeyboardButton(text="🧠 DeepSeek", callback_data="ask_deepseek"),
        ]
    ])


def city_keyboard():
    kb = [
        [KeyboardButton(text=name)] for name in CITIES.keys()
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


# === /start ===
@dp.message(Command("start"))
async def cmd_start(message: Message):
    now = datetime.now()
    weekday_en = now.strftime("%A")
    weekday_ru = WEEKDAYS_RU.get(weekday_en, weekday_en)
    date_str = now.strftime("%d.%m.%Y") + f" ({weekday_ru})"

    await message.answer(
        f"Привет! "
        f"Сегодня {date_str}\n"
        f"Запуск: {ENVIRONMENT}\n"
        f"Ответ сервера: RENDER",
        reply_markup=main_keyboard()
    )
    await message.answer("Попробуй ИИ:", reply_markup=ai_keyboard())


# === Callback-кнопки ChatGPT / DeepSeek ===
@dp.callback_query(lambda c: c.data in ["ask_gpt", "ask_deepseek"])
async def ask_ai(callback_query: types.CallbackQuery):
    service = "ChatGPT" if callback_query.data == "ask_gpt" else "DeepSeek"
    await callback_query.message.answer(f"Ты выбрал {service}. Напиши свой вопрос.")
    user_choice[callback_query.from_user.id] = callback_query.data


# === Обработчик текста ===
@dp.message()
async def process_user_message(message: Message):
    choice = user_choice.get(message.from_user.id)
    if choice:
        if choice == "ask_gpt":
            await message.answer("Жду ответ от ChatGPT...")
            answer = await call_chatgpt_api(message.text)
            await message.answer(answer)
        elif choice == "ask_deepseek":
            await message.answer("Жду ответ от DeepSeek...")
            answer = await call_deepseek_api(message.text)
            await message.answer(answer)
        user_choice.pop(message.from_user.id, None)
        return

    # --- Обработка кнопок меню ---
    if message.text == "🔮 Психонетика Инь-Ян":
        await message.answer(
            "Присоединяйтесь к группе:\nhttps://t.me/+EL9esd0xZ-xkMTU6",
            reply_markup=main_keyboard()
        )

    elif message.text == "🌲 Иркутск психотехнологии":
        await message.answer(
            "Присоединяйтесь к группе:\nhttps://t.me/+7ZBrobhAJoRhM2U6",
            reply_markup=main_keyboard()
        )

    elif message.text == "🌤 Погода":
        await message.answer("Выберите город:", reply_markup=city_keyboard())

    elif message.text in CITIES:
        await show_weather(message)

    elif message.text == "💵 Курс валют":
        await show_currency(message)

    elif message.text == "💬 Цитата":
        await send_random_quote(message)

    elif message.text == "🤖 Выбор ИИ":
        await message.answer("Выбери ИИ:", reply_markup=ai_keyboard())

    elif message.text == "❓ Помощь":
        await show_help(message)


# === Погода ===
async def show_weather(message: Message):
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
        await message.answer(f"Ошибка погоды: {e}", reply_markup=main_keyboard())


# === Курс валют ===
async def show_currency(message: Message):
    data = requests.get("https://www.cbr-xml-daily.ru/daily_json.js").json()
    usd = data['Valute']['USD']['Value']
    eur = data['Valute']['EUR']['Value']
    await message.answer(f"USD: {usd:.2f}₽\nEUR: {eur:.2f}₽", reply_markup=main_keyboard())


# === Цитаты ===
async def send_random_quote(message: Message):
    quotes = load_quotes()
    if not quotes:
        await message.answer("Нет цитат.", reply_markup=main_keyboard())
        return
    q = random.choice(quotes)
    text = q['text'] if isinstance(q, dict) else str(q)
    await message.answer(f"«{text}»", reply_markup=main_keyboard())


# === Помощь ===
async def show_help(message: Message):
    await message.answer("Помощь: /start, погода, курс валют, цитаты", reply_markup=main_keyboard())


# === Вызовы API ===
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
        "messages": [
            {"role": "system",
             "content": "Ты — искусственный интеллект DeepSeek. Отвечай как DeepSeek и не упоминай GPT или OpenAI."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            r = await resp.json()
            return r["choices"][0]["message"]["content"]


# @app.on_event("startup") - версия с предупреждением
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при старте приложения
    await bot.set_webhook(WEBHOOK_URL)
    yield



@app.get("/")
def root():
    return {"status": "ok", "bot": "running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
