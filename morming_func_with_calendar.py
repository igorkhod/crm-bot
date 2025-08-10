import os
import json
import random
import requests
from datetime import datetime
from pathlib import Path
import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv(Path(__file__).parent / 'token.env')

# Инициализация бота с токеном из переменных окружения
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Получение API-ключа для погоды
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Путь к файлу с цитатами
QUOTES_FILE = Path(__file__).parent / 'quotes.json'


# Функция загрузки цитат из JSON-файла
def load_quotes():
    """Загружает цитаты из файла quotes.json"""
    try:
        if QUOTES_FILE.exists():
            with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Ошибка загрузки цитат: {e}")
        return []


# Функция создания клавиатуры с кнопками
def create_keyboard():
    """Создает и возвращает Reply-клавиатуру с основными кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("📅 Календарь"),
        types.KeyboardButton("🌤 Погода"),
        types.KeyboardButton("💬 Случайная цитата"),
        types.KeyboardButton("❓ Помощь")
    ]
    markup.add(*buttons)
    return markup


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    """Отправляет приветственное сообщение и клавиатуру"""
    bot.send_message(
        chat_id=message.chat.id,
        text="Добро пожаловать! Выберите действие:",
        reply_markup=create_keyboard()
    )


# Обработчик кнопки "Календарь"
@bot.message_handler(func=lambda m: m.text == "📅 Календарь")
def show_calendar(message):
    """Отправляет интерактивный календарь"""
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(
        chat_id=message.chat.id,
        text=f"Выберите {LSTEP[step]}",
        reply_markup=calendar
    )


# Обработчик выбора даты в календаре
@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def handle_calendar(call):
    """Обрабатывает выбор даты в календаре"""
    result, key, step = DetailedTelegramCalendar().process(call.data)

    if not result and key:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Выберите {LSTEP[step]}",
            reply_markup=key
        )
    elif result:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📅 Вы выбрали: {result.strftime('%d.%m.%Y')}"
        )
        bot.send_message(
            chat_id=call.message.chat.id,
            text="Что дальше?",
            reply_markup=create_keyboard()
        )


# Обработчик кнопки "Погода"
@bot.message_handler(func=lambda m: m.text == "🌤 Погода")
def ask_city_for_weather(message):
    """Запрашивает город для показа погоды"""
    msg = bot.send_message(
        chat_id=message.chat.id,
        text="Введите название города:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_city_input)


def process_city_input(message):
    """Получает погоду для указанного города"""
    city = message.text
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        temp = data['main']['temp']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']

        weather_text = (
            f"🌤 Погода в {city}:\n"
            f"• Температура: {temp}°C\n"
            f"• Описание: {description}\n"
            f"• Влажность: {humidity}%"
        )
        bot.send_message(
            chat_id=message.chat.id,
            text=weather_text,
            reply_markup=create_keyboard()
        )
    except Exception as e:
        bot.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ Не удалось получить погоду для {city}. Попробуйте другой город.",
            reply_markup=create_keyboard()
        )


# Обработчик кнопки "Случайная цитата"
@bot.message_handler(func=lambda m: m.text == "💬 Случайная цитата")
def send_random_quote(message):
    """Отправляет случайную цитату из файла"""
    quotes = load_quotes()

    if not quotes:
        bot.send_message(
            chat_id=message.chat.id,
            text="📭 Цитаты не найдены. Файл quotes.json пуст или отсутствует.",
            reply_markup=create_keyboard()
        )
        return

    # Выбираем случайную цитату
    quote = random.choice(quotes)

    # Форматируем вывод в зависимости от структуры цитаты
    if isinstance(quote, dict):
        quote_text = quote.get('text', 'Текст цитаты отсутствует')
        author = quote.get('author', 'Неизвестный автор')
        response = f"💬 Цитата:\n\n«{quote_text}»\n— {author}"
    else:
        response = f"💬 Цитата:\n\n«{quote}»"

    bot.send_message(
        chat_id=message.chat.id,
        text=response,
        reply_markup=create_keyboard()
    )


# Обработчик кнопки "Помощь"
@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def show_help(message):
    """Отправляет справочное сообщение"""
    help_text = (
        "ℹ️ Справка по боту:\n\n"
        "📅 Календарь - выбрать дату\n"
        "🌤 Погода - узнать погоду в любом городе\n"
        "💬 Случайная цитата - получить случайную цитату\n"
        "❓ Помощь - это сообщение"
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=help_text,
        reply_markup=create_keyboard()
    )


# Запуск бота
if __name__ == '__main__':
    print("✅ Бот запущен и готов к работе!")
    bot.polling(none_stop=True)