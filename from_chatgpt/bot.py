import asyncio
import json
import os
import random
from datetime import datetime
from pathlib import Path

import aiohttp
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from db import init_db, update_visitor, start_session, update_session, get_stats
# версия от17:16 30.07.2025
# ========== Загрузка окружения ==========
local_env = Path(__file__).parent / "token_local.env"
prod_env = Path(__file__).parent / "token.env"

if local_env.exists():
    ENVIRONMENT = "LOCAL"
    load_dotenv(local_env)
    env_file = local_env
elif prod_env.exists():
    ENVIRONMENT = "PROD_LOCAL"
    load_dotenv(prod_env)
    env_file = prod_env
else:
    ENVIRONMENT = "RENDER"
    load_dotenv("/etc/secrets/token.env")
    env_file = Path("/etc/secrets/token.env")

print(f"Использую секреты: {env_file}")
print(f"Режим запуска: {ENVIRONMENT}")

# ========== Константы ==========
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://telegram-cloud-bot-kwcs.onrender.com/webhook"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# <<< Сразу после создания dp вставляешь init_db() >>>
init_db()

if ENVIRONMENT == "RENDER":
    from fastapi import FastAPI, Request
    from contextlib import asynccontextmanager


    @asynccontextmanager
    async def lifespan(app: "FastAPI"):
        await bot.set_webhook(WEBHOOK_URL)
        yield


    app = FastAPI(lifespan=lifespan)

CITIES = {"Красноярск": "Krasnoyarsk", "Иркутск": "Irkutsk"}
WEEKDAYS_RU = {
    "Monday": "Понедельник", "Tuesday": "Вторник",
    "Wednesday": "Среда", "Thursday": "Четверг",
    "Friday": "Пятница", "Saturday": "Суббота",
    "Sunday": "Воскресенье",
}
QUOTES_FILE = Path(__file__).parent / "data" / "quotes.json"
user_choice = {}


# ========== Клавиатуры ==========
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Психонетика Инь-Ян", callback_data="group_psy"),
         InlineKeyboardButton(text="🌲 Иркутск психотехнологии", callback_data="group_irkutsk")],
        [InlineKeyboardButton(text="🌤 Погода", callback_data="weather"),
         InlineKeyboardButton(text="💵 Курс валют", callback_data="currency")],
        [InlineKeyboardButton(text="💬 Цитата", callback_data="quote")],
        [InlineKeyboardButton(text="🤖 ChatGPT", callback_data="ask_gpt"),
         InlineKeyboardButton(text="🧠 DeepSeek", callback_data="ask_deepseek")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])


def city_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"city:{name}")] for name in CITIES.keys()
    ])


def load_quotes():
    if QUOTES_FILE.exists():
        try:
            with open(QUOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


async def animate_dots(chat_id, text, stop_event: asyncio.Event):
    dots = ["•", "●", "●●", "●●●"]
    msg = await bot.send_message(chat_id, f"{text} …")
    while not stop_event.is_set():
        for dot in dots:
            if stop_event.is_set():
                break
            try:
                await msg.edit_text(f"{text} {dot}")
                await asyncio.sleep(0.25)
            except:
                return msg
    return msg


# ========== /start ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    # --- заплатка: записываем пользователя и начинаем сессию ---
    update_visitor(message.from_user.id, message.from_user.username or "")
    start_session(message.from_user.id)
    # --- конец заплатки ---
    now = datetime.now()
    weekday = WEEKDAYS_RU[now.strftime("%A")]
    date_str = now.strftime("%d.%m.%Y") + f" ({weekday})"

    await message.answer(f"Привет! Сегодня {date_str}", reply_markup=main_keyboard())
# ========== /start ==========
# ========== /stats начало ==========
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    loop = asyncio.get_running_loop()
    # выполняем get_stats в пуле потоков
    stats = await loop.run_in_executor(None, get_stats)
    count, first_seen, session_count, first_session, total_seconds = stats
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    await message.answer(
        f"Пользователей: {count}\nПервый визит: {first_seen}\n\n"
        f"Сессий: {session_count}\nПервый сеанс: {first_session}\n"
        f"Время в боте: {h} ч {m} мин"
    )
    # ========== /stats конец==========
# ========== Callback Query (основная логика кнопок) ==========
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    # --- заплатка: обновляем время активности ---
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, update_session, callback.from_user.id)
    # --- конец заплатки ---

    data = callback.data

    if data == "group_psy":
        await callback.message.edit_text(
            "Присоединяйтесь:\nhttps://t.me/+EL9esd0xZ-xkMTU6",
            reply_markup=main_keyboard())
        return

    if data == "group_irkutsk":
        await callback.message.edit_text(
            "Присоединяйтесь:\nhttps://t.me/+7ZBrobhAJoRhM2U6",
            reply_markup=main_keyboard())
        return

    if data == "weather":
        await callback.message.edit_text("Выберите город:", reply_markup=city_keyboard())
        return

    if data.startswith("city:"):
        city = data.split(":", 1)[1]
        await show_weather(callback.message, city)
        return

    if data == "currency":
        await show_currency(callback.message)
        return

    if data == "quote":
        await send_random_quote(callback.message)
        return

    if data == "ask_gpt":
        user_choice[callback.from_user.id] = "ask_gpt"
        await callback.message.edit_text("Ты выбрал ChatGPT. Напиши вопрос текстом.")
        return

    if data == "ask_deepseek":
        user_choice[callback.from_user.id] = "ask_deepseek"
        await callback.message.edit_text("Ты выбрал DeepSeek. Напиши вопрос текстом.")
        return

    if data == "help":
        await show_help(callback.message)
        return


# ========== Обычные сообщения (для ИИ) ==========
@dp.message()
async def process_user_message(message: Message):
    # --- заплатка: обновляем время активности ---
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, update_session, message.from_user.id)
    # --- конец заплатки ---

    choice = user_choice.get(message.from_user.id)

    if choice == "ask_gpt":
        stop = asyncio.Event()
        task = asyncio.create_task(animate_dots(message.chat.id, "Жду ответ от ChatGPT", stop))
        answer = await call_chatgpt_api(message.text)
        stop.set()
        msg = await task
        await msg.edit_text(answer)
        user_choice.pop(message.from_user.id, None)
        return

    if choice == "ask_deepseek":
        stop = asyncio.Event()
        task = asyncio.create_task(animate_dots(message.chat.id, "Жду ответ от DeepSeek", stop))
        answer = await call_deepseek_api(message.text)
        stop.set()
        msg = await task
        await msg.edit_text(answer)
        user_choice.pop(message.from_user.id, None)
        return


# ========== Функции ==========
async def show_weather(msg, city):
    code = CITIES[city]
    url = f"http://api.openweathermap.org/data/2.5/weather?q={code},RU&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    r = requests.get(url).json()
    temp = r["main"]["temp"]
    desc = r["weather"][0]["description"].capitalize()
    await msg.edit_text(f"Погода в {city}: {temp:.1f}°C, {desc}", reply_markup=main_keyboard())


async def show_currency(msg):
    data = requests.get("https://www.cbr-xml-daily.ru/daily_json.js").json()
    usd, eur = data["Valute"]["USD"]["Value"], data["Valute"]["EUR"]["Value"]
    await msg.edit_text(f"USD: {usd:.2f}₽\nEUR: {eur:.2f}₽", reply_markup=main_keyboard())


async def send_random_quote(msg):
    q = random.choice(load_quotes() or ["Нет цитат"])
    text = q["text"] if isinstance(q, dict) else q
    await msg.edit_text(f"«{text}»", reply_markup=main_keyboard())


async def show_help(msg):
    await msg.edit_text("Помощь: выберите команду из меню", reply_markup=main_keyboard())


# ========== AI API ==========
async def call_chatgpt_api(prompt: str) -> str:
    key = os.getenv("IGOR_OPENAI_API")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 200}
    async with aiohttp.ClientSession() as s:
        async with s.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as r:
            return (await r.json())["choices"][0]["message"]["content"]


async def call_deepseek_api(prompt: str) -> str:
    key = os.getenv("IGOR_KHOD_DEEPSEEK_API_KEY")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat",
            "messages": [{"role": "system", "content": "Ты DeepSeek."}, {"role": "user", "content": prompt}],
            "max_tokens": 200}
    async with aiohttp.ClientSession() as s:
        async with s.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data) as r:
            return (await r.json())["choices"][0]["message"]["content"]


# ========== Webhook ==========
if ENVIRONMENT == "RENDER":
    @app.post(WEBHOOK_PATH)
    async def webhook(request: Request):
        data = await request.json()
        await dp.feed_webhook_update(bot, types.Update(**data))
        return {"ok": True}


    @app.get("/")
    def root():
        return {"status": "ok", "bot": "running"}

if __name__ == "__main__":
    if ENVIRONMENT in ["LOCAL", "PROD_LOCAL"]:
        print("LOCAL POLLING...")
        asyncio.run(dp.start_polling(bot))
    else:
        import uvicorn

        print("RENDER WEBHOOK...")
        uvicorn.run(app, host="0.0.0.0", port=10000)
