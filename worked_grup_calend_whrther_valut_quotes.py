import os
import json
import random
from datetime import datetime
from pathlib import Path
import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from dotenv import load_dotenv
import requests
import time  # Добавьте в импорты
from pytils.dt import ru_strftime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from db import update_visitor

# Загрузка переменных окружения
load_dotenv(Path(__file__).parent / 'token.env')
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CURRENCY_API = "https://www.cbr-xml-daily.ru/daily_json.js"
QUOTES_FILE = Path(__file__).parent / 'quotes.json'
# Глобальный словарь для кеша погоды
WEATHER_CACHE = {}

# Список доступных городов для погоды
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


def get_cached_weather(city_code):
    """Получает погоду из кеша, если она актуальна"""
    cached = WEATHER_CACHE.get(city_code)
    if cached and (time.time() - cached['timestamp']) < 3600:  # 1 час
        return cached['data']
    return None


def cache_weather(city_code, data):
    """Сохраняет погоду в кеш"""
    WEATHER_CACHE[city_code] = {
        'data': data,
        'timestamp': time.time()
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
        types.KeyboardButton("💵 Курс валют"),
        types.KeyboardButton("💬 Случайная цитата"),
        types.KeyboardButton("❓ Помощь")
    ]
    markup.add(*buttons)
    return markup


@bot.message_handler(func=lambda m: m.text == "🔮🕉️ Перейти в группу Психонетика Инь-Ян")
def go_to_psychonetics(message):
    group_link = "https://t.me/+EL9esd0xZ-xkMTU6"

    # Правильное экранирование для MarkdownV2
    escaped_link = group_link.replace('-', r'\-').replace('.', r'\.').replace('_', r'\_')

    text = (
            r"🔮 Группа «Психонетика Инь\-Ян»:" + "\n\n"
                                                 f"[Нажмите здесь]({escaped_link}) для перехода" + "\n\n"
                                                                                                   r"_Если ссылка не работает, скопируйте её вручную:_" + "\n"
                                                                                                                                                          f"`{escaped_link}`"
    )

    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        parse_mode="MarkdownV2",
        reply_markup=create_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🌲⚙️ Перейти в группу Иркутск психотехнологии")
def go_to_irkutsk(message):
    group_link = "https://t.me/+7ZBrobhAJoRhM2U6"
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


# обработчик команды /start"

@dp.message(Command("start"))
async def cmd_start(message: Message):
    # Обновляем информацию о пользователе
    update_visitor(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    today = datetime.now().strftime("%d.%m.%Y")
    await message.answer(
        f"Привет! Я работаю через WEBHOOK ☁️\nСегодня {today}\nОтвет сервера: RENDER",
        reply_markup=main_keyboard()
    )
    await message.answer("Попробуй ИИ:", reply_markup=ai_keyboard())


# конец блока обработчика команды /start"

@bot.message_handler(func=lambda m: m.text == "📅 Календарь")
def calendar_handler(message):
    """Обработка кнопки календаря"""
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    bot.send_message(
        message.chat.id,
        f"Календарь: Выберите год",
        # f"Календарь 2: Выбор  {LSTEP[step]}",
        reply_markup=calendar

    )


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def calendar_callback(call):
    """Обработка выбора даты в календаре"""
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text(
            f"Выберите {LSTEP[step]}",
            # f"Выберите месяц, день",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=key
        )
    elif result:
        bot.edit_message_text(
            f"📅 Выбрано: {result.strftime('%d.%m.%Y')}",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(
            call.message.chat.id,
            "Что дальше?",
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


# -------------погода--------------------------

@bot.message_handler(func=lambda m: m.text in ["Красноярск", "Иркутск"])
def show_weather(message):
    """Показ погоды для выбранного города"""
    try:
        city_name = message.text
        city_code = CITIES.get(city_name)

        if not city_code:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"⚠️ Город {city_name} не найден в списке",
                reply_markup=create_keyboard()
            )
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_code},RU&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            error_msg = data.get('message', 'Неизвестная ошибка API')
            raise Exception(f"API Error {response.status_code}: {error_msg}")

        temp = data['main']['temp']
        description = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        wind = data['wind']['speed']

        weather_text = (
            f"🌤 Погода в {city_name}:\n"
            f"• Температура: {round(temp, 1)}°C\n"
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
        # Логирование ошибки
        error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_details = f"Time: {error_time}, City: {city_name}, Error: {str(e)}"
        print(f"⛈ Weather API Error: {error_details}")

        # Формируем сообщение об ошибке
        if "404" in str(e):
            error_msg = "Город не найден в базе погоды"
        elif "401" in str(e):
            error_msg = "Проблема с API-ключом погоды"
        else:
            error_msg = "Сервис погоды временно недоступен"

        # Отправка сообщения пользователю
        bot.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ Не удалось получить погоду для {city_name}\n"
                 f"Причина: {error_msg}\n"
                 f"Попробуйте позже",
            reply_markup=create_keyboard()
        )

        # Отправка уведомления администратору
        admin_chat_id = os.getenv("ADMIN_ID")  # Чтение из token.env
        if admin_chat_id:
            try:
                bot.send_message(
                    chat_id=int(admin_chat_id),
                    text=f"🚨 Ошибка погоды:\n{error_details}"
                )
            except Exception as admin_error:
                print(f"Ошибка отправки админу: {admin_error}")


# ------------------конец блока погода--------------

@bot.message_handler(func=lambda m: m.text == "💵 Курс валют")
def show_currency(message):
    try:
        response = requests.get(CURRENCY_API)
        data = response.json()

        usd = data['Valute']['USD']['Value']
        eur = data['Valute']['EUR']['Value']
        cny = data['Valute']['CNY']['Value']

        text = (
            "📊 Курс ЦБ РФ:\n"
            f"• USD: {usd:.2f} ₽\n"
            f"• EUR: {eur:.2f} ₽\n"
            f"• CNY: {cny:.2f} ₽\n"
            f"\n🔄 Обновлено: {data['Date'][:10]}"
        )
        bot.send_message(message.chat.id, text, reply_markup=create_keyboard())
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка: {str(e)}", reply_markup=create_keyboard())


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
