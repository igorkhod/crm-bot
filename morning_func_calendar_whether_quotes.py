import os
import json
import random
from email import message

import requests
from datetime import datetime
from pathlib import Path
import telebot
from pytils.dt import ru_strftime
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from dotenv import load_dotenv

from good_morning_2 import KEYBOARD

# Загрузка переменных окружения
load_dotenv(Path(__file__).parent / 'token.env')
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
QUOTES_FILE = Path(__file__).parent / 'quotes.json'

# Список доступных городов для погоды
CITIES = {
    "Красноярск": "Krasnoyarsk",
    "Иркутск": "Irkutsk"
}


def load_quotes():
    """Загружает цитаты из файла"""
    try:
        if QUOTES_FILE.exists():
            with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Ошибка загрузки цитат: {e}")
        return []


def create_keyboard():
    """Основная клавиатура"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("🔮🕉️ Перейти в группу Психонетика Инь-Ян"),
        types.KeyboardButton("🌲⚙️ Перейти в группу Иркутск психотехнологии"),
        types.KeyboardButton("📅 Календарь"),
        types.KeyboardButton("🌤 Погода"),
        types.KeyboardButton("💬 Случайная цитата"),
        types.KeyboardButton("❓ Помощь")
    ]
    markup.add(*buttons)
    return markup


@bot.message_handler(func=lambda m: m.text == "🔮🕉️ Перейти в группу Психонетика Инь-Ян")
def go_to_psychonetics(message):
    group_link = "https://t.me/+EL9esd0xZ-xkMTU6"  # Замените на реальную ссылку
    bot.send_message(
        chat_id=message.chat.id,
        text=f"🔮 Присоединяйтесь к группе 'Психонетика Инь-Ян':\n{group_link}",
        reply_markup=create_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🌲⚙️ Перейти в группу Иркутск психотехнологии")
def go_to_irkutsk(message):
    group_link = "https://t.me/+7ZBrobhAJoRhM2U6"  # Замените на реальную ссылку
    bot.send_message(
        chat_id=message.chat.id,
        text=f"🌲 Присоединяйтесь к группе 'Иркутск психотехнологии':\n{group_link}",
        reply_markup=create_keyboard()
    )


def create_city_keyboard():
    """Клавиатура для выбора города"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("Красноярск"),
        types.KeyboardButton("Иркутск"),
        types.KeyboardButton("↩️ Назад")
    ]
    markup.add(*buttons)
    return markup


# -------------------------------------------------

@bot.message_handler(commands=['start'])
def start(message):
    """Обработка команды /start"""
    today = datetime.now()
    date_str = today.strftime("%d.%m.%Y")
    """начало для календаря"""
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    bot.send_message(message.chat.id,
                     f"Календарь 2: Выборите год",
                     # f"Календарь 2: Выбор  {LSTEP[step]}",
                     reply_markup=calendar)

    bot.send_message(
        chat_id=message.chat.id,
        text=f"Добро пожаловать! Выберите действие:\nСегодня {date_str}",
        reply_markup=create_keyboard()
    )


# --------календарь------------------------------------------
@bot.message_handler(func=lambda m: m.text == "📅 Календарь")
def calendar_handler(message):
    """Обработка кнопки календаря"""
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id,
                     f"Выберите {LSTEP[step]}",
                     reply_markup=calendar)

    # @bot.message_handler(func=lambda m: m.text == "📅 Календарь")
    # def show_calendar(message):
    #     """Показ календаря"""
    #     calendar, step = DetailedTelegramCalendar().build()
    #     bot.send_message(
    #         chat_id=message.chat.id,
    #         text=f"Выберите {LSTEP[step]}",
    #         reply_markup=calendar
    #     )

    @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
    def calendar_callback(call):
        """Обработка выбора даты в календаре"""
        result, key, step = DetailedTelegramCalendar().process(call.data)
        if not result and key:
            bot.edit_message_text(f"Выберите {LSTEP[step]}",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=key)
        elif result:
            bot.edit_message_text(f"📅 Выбрано: {result.strftime('%d.%m.%Y')}",
                                  call.message.chat.id,
                                  call.message.message_id)
            bot.send_message(call.message.chat.id,
                             "Что дальше?",
                             reply_markup=main_keyboard())

    @bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
    def cal1(c):
        # calendar_id is used here too, since the new keyboard is made
        result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(c.data)
        if not result and key:
            bot.edit_message_text(f"Календарь 2: Выберите {LSTEP[step]}",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            bot.edit_message_text(f"Вы выбрали дату {result} в календаре ",
                                  c.message.chat.id,
                                  c.message.message_id)

        bot.send_message(
            chat_id=call.message.chat.id,
            text="Что дальше?",
            reply_markup=create_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "🌤 Погода")
def ask_city_for_weather(message):
    """Запрос города для погоды"""
    bot.send_message(
        chat_id=message.chat.id,
        text="Выберите город:",
        reply_markup=create_city_keyboard()
    )


@bot.message_handler(func=lambda m: m.text in ["Красноярск", "Иркутск"])
def show_weather(message):
    """Показ погоды для выбранного города"""
    city_name = message.text
    city_code = CITIES[city_name]

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_code}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        temp = data['main']['temp']
        description = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        wind = data['wind']['speed']

        weather_text = (
            f"🌤 Погода в {city_name}:\n"
            f"• Температура: {temp}°C\n"
            f"• Состояние: {description}\n"
            f"• Влажность: {humidity}%\n"
            f"• Ветер: {wind} м/с"
        )
        bot.send_message(
            chat_id=message.chat.id,
            text=weather_text,
            reply_markup=create_keyboard()
        )
    except Exception as e:
        bot.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ Ошибка при получении погоды для {city_name}",
            reply_markup=create_keyboard()
        )


@bot.message_handler(func=lambda m: m.text == "↩️ Назад")
def back_to_main(message):
    """Возврат в главное меню"""
    bot.send_message(
        chat_id=message.chat.id,
        text="Выберите действие:",
        reply_markup=create_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "💬 Случайная цитата")
def send_random_quote(message):
    """Отправка случайной цитаты"""
    quotes = load_quotes()

    if not quotes:
        bot.send_message(
            chat_id=message.chat.id,
            text="📭 Цитаты не найдены",
            reply_markup=create_keyboard()
        )
        return

    quote = random.choice(quotes)
    if isinstance(quote, dict):
        text = quote.get('text', 'Без текста')
        # author = quote.get('author', 'Неизвестный автор')
        # response = f"💬 Цитата:\n\n«{text}»\n— {author}"
        response = f"💬 Цитата:\n\n«{text}»\n—"
    else:
        response = f"💬 Цитата:\n\n«{quote}»"

    bot.send_message(
        chat_id=message.chat.id,
        text=response,
        reply_markup=create_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def show_help(message):
    """Показ справки"""
    help_text = (
        "ℹ️ Справка по боту:\n\n"
        "📅 Календарь - выбрать дату\n"
        "🌤 Погода - узнать погоду\n"
        "💬 Случайная цитата - получить цитату\n"
        "❓ Помощь - это сообщение"
    )
    bot.send_message(
        chat_id=message.chat.id,
        text=help_text,
        reply_markup=create_keyboard()
    )


if __name__ == '__main__':
    print("✅ Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
