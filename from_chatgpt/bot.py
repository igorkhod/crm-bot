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

# Загружаем секреты из файла Render
load_dotenv("/etc/secrets/token.env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://telegram-cloud-bot-kwcs.onrender.com/webhook"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# ---- Временное хранилище выбора пользователя ----
user_choice = {}

# ---- Папка с цитатами ----
QUOTES_FILE = Path(__file__).parent / "data" / "quotes.json"

# ---- Города ----
CITIES = {
    "Красноярск": "Krasnoyarsk",
    "Иркутск": "Irkutsk"
}

# ==== Клавиатуры ====

def main_keyboard():
    kb = [
        [KeyboardButton(text="🌤 Погода"),
         KeyboardButton(text="💵 Курс валют")],
        [KeyboardButton(text="💬 Цитата"),
         KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def ai_keyboard():
    return InlineKeybo
