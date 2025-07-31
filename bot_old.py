import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
import uvicorn
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import requests
import json
import random

# Загружаем секреты
load_dotenv("/etc/secrets/token.env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Webhook параметры
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://telegram-cloud-bot-kwcs.onrender.com/webhook"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# ===== Клавиатуры =====
def main_keyboard():
    kb = [
        [KeyboardButton(text="🌤 Погода"),
         KeyboardButton(text="💵 Курс валют")],
        [KeyboardButton(text="💬 Цитата"),
         KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

CITIES = {
    "Красноярск": "Krasnoyarsk",
    "Иркутск": "Irkutsk"
}

QUOTES_FILE = Path(__file__).parent / "data" / "quotes.json"

def load_quotes():
    if QUOTES_FILE.exists():
        try:
            with open(QUOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

# ===== Команды =====
@dp.message(Command("start"))
async def cmd_start(message: Message):
    today = datetime.now().strftime("%d.%m.%Y")
    await message.answer(
        f"Привет! Я работаю через WEBHOOK ☁️\nСегодня {today}\nОтвет сервера: RENDER",
        reply_markup=main_keyboard()
    )

@dp.message(lambda m: m.text == "🌤 Погода")
async def ask_city(message: Message):
    kb = [[KeyboardButton(text=city)] for city in CITIES]
    await message.answer("Выберите город:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

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
        await message.answer(f"Ошибка погоды: {e}", reply_markup=main_keyboard())

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
    await message.answer("Помощь: /start, погода, курс валют, цитаты", reply_markup=main_keyboard())

# ===== Webhook обработчик =====
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    await dp.feed_webhook_update(bot, types.Update(**data))
    return {"ok": True}

# Устанавливаем webhook при старте
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

# Проверка работы
@app.get("/")
def root():
    return {"status": "ok", "mode": "webhook"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
