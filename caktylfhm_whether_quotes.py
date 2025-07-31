import os
import json
import random
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image
import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from dotenv import load_dotenv

# --- Инициализация ---
load_dotenv(Path(__file__).parent / 'token.env')
bot = telebot.TeleBot(os.getenv("TOKEN"))
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
QUOTES_FILE = Path(__file__).parent / 'quotes.json'
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

# Конфигурация городов
CITIES = {
    "Красноярск": {
        "code": "Krasnoyarsk",
        "emoji": "🏙️"
    },
    "Иркутск": {
        "code": "Irkutsk",
        "emoji": "🏔️"
    }
}

# Ссылки на изображения городов
CITY_IMAGES = {
    "Красноярск": {
        "url": "https://avatars.mds.yandex.net/i?id=1ca589f37177ebbb703224197d6f24d4_l-4824599-images-thumbs&n=13",
        "path": "data/krasnoyarsk.jpg"
    },
    "Иркутск": {
        "url": "https://rused.ru/irk-mdou96/wp-content/uploads/sites/129/2020/05/1430939158_gerb-8.jpg",
        "path": "data/irkutsk.jpg"
    }
}

# Ссылки на группы
GROUP_LINKS = {
    "🧠 Психонетика Инь-Ян": "https://t.me/+EL9esd0xZ-xkMTU6",
    "🔮 Иркутск психотех": "https://t.me/+7ZBrobhAJoRhM2U6"
}

# Создаем папку для данных
os.makedirs("data", exist_ok=True)


# --- Функции загрузки изображений ---
def download_and_resize_images():
    """Загружает и уменьшает изображения городов (только при первом запуске)"""
    for city, data in CITY_IMAGES.items():
        if not os.path.exists(data["path"]):
            try:
                print(f"Загрузка изображения для {city}...")
                response = requests.get(data["url"], timeout=10)
                img = Image.open(BytesIO(response.content))

                # Уменьшаем размер в 2 раза с сохранением пропорций
                new_size = (img.width // 2, img.height // 2)
                img = img.resize(new_size, Image.LANCZOS)

                img.save(data["path"], "JPEG", quality=85)
                print(f"Изображение для {city} сохранено")
            except Exception as e:
                print(f"Ошибка загрузки изображения для {city}: {e}")


# Вызываем при старте
download_and_resize_images()


# --- Клавиатуры ---
def main_keyboard():
    """Главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("📅 Календарь"),
        types.KeyboardButton("🌤 Погода"),
        types.KeyboardButton("💬 Цитата"),
        types.KeyboardButton("💰 Валюта"),
        types.KeyboardButton("❓ Помощь"),
        *[types.KeyboardButton(name) for name in GROUP_LINKS.keys()]
    ]
    markup.add(*buttons)
    return markup


def cities_keyboard():
    """Клавиатура выбора города"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(f"{city} {data['emoji']}") for city, data in CITIES.items()]
    buttons.append(types.KeyboardButton("↩️ Назад"))
    markup.add(*buttons)
    return markup


# --- Функции данных ---
def load_quotes():
    """Загрузка цитат из файла"""
    try:
        if QUOTES_FILE.exists():
            with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Ошибка загрузки цитат: {e}")
        return []


def get_weather(city_name):
    """Получение данных о погоде"""
    try:
        city_data = CITIES[city_name]
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_data['code']}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url, timeout=5)
        data = response.json()

        return {
            "text": (
                f"{city_data['emoji']} Погода в {city_name}:\n"
                f"• {data['weather'][0]['description'].capitalize()}\n"
                f"• Температура: {data['main']['temp']}°C\n"
                f"• Ощущается как: {data['main']['feels_like']}°C\n"
                f"• Влажность: {data['main']['humidity']}%\n"
                f"• Ветер: {data['wind']['speed']} м/с"
            ),
            "image_path": CITY_IMAGES[city_name]["path"]
        }
    except Exception as e:
        print(f"Ошибка погоды: {e}")
        return None


def get_currency_rates():
    """Получение курсов валют от ЦБ РФ"""
    try:
        response = requests.get(CBR_API_URL, timeout=5)
        data = response.json()

        usd = data['Valute']['USD']
        eur = data['Valute']['EUR']

        return (
            "💱 Курсы ЦБ РФ:\n\n"
            f"🇺🇸 USD: {usd['Value']} ₽\n"
            f"🇪🇺 EUR: {eur['Value']} ₽\n\n"
            f"📅 Обновлено: {data['Date'][:10]}"
        )
    except Exception as e:
        print(f"Ошибка получения курсов: {e}")
        return None


# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def start(message):
    """Обработка команды /start"""
    bot.send_message(message.chat.id,
                     "Добро пожаловать! Выберите действие:",
                     reply_markup=main_keyboard())


@bot.message_handler(func=lambda m: m.text == "📅 Календарь")
def calendar_handler(message):
    """Обработка кнопки календаря"""
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id,
                     f"Выберите {LSTEP[step]}",
                     reply_markup=calendar)


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


@bot.message_handler(func=lambda m: m.text == "🌤 Погода")
def weather_handler(message):
    """Обработка кнопки погоды"""
    bot.send_message(message.chat.id,
                     "Выберите город:",
                     reply_markup=cities_keyboard())
#обработка вывода города
#-----------------------------------------------------------------

@bot.message_handler(func=lambda m: any(city in m.text for city in CITIES))
def city_handler(message):
    """Обработка выбора города с картинкой слева и текстом справа"""
    city_name = next((city for city in CITIES if city in message.text), None)

    if not city_name or not (weather_data := get_weather(city_name)):
        return bot.send_message(message.chat.id, "⚠️ Данные недоступны", reply_markup=main_keyboard())

    try:
        # Создаем временное изображение с уменьшенным размером
        with open(CITY_IMAGES[city_name]["path"], 'rb') as img_file:
            # Отправляем фото с кастомным caption справа
            bot.send_photo(
                chat_id=message.chat.id,
                photo=img_file,
                caption=weather_data["text"],
                reply_markup=main_keyboard(),
                parse_mode='HTML'
            )

    except Exception as e:
        print(f"Ошибка отправки: {e}")
        # Фолбэк: раздельная отправка
        with open(CITY_IMAGES[city_name]["path"], 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
        bot.send_message(message.chat.id, weather_data["text"], reply_markup=main_keyboard())

#конец обработки вывода города
#-----------------------------------------------------------------

@bot.message_handler(func=lambda m: m.text == "💬 Цитата")
def quote_handler(message):
    """Обработка кнопки цитаты"""
    quotes = load_quotes()
    if quotes:
        quote = random.choice(quotes)
        text = f"💬 Цитата дня:\n\n«{quote['text']}»\n— {quote.get('author', 'Неизвестный автор')}"
    else:
        text = "📭 Цитаты не найдены"
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())


@bot.message_handler(func=lambda m: m.text == "💰 Валюта")
def currency_handler(message):
    """Обработка кнопки валюты"""
    if rates := get_currency_rates():
        bot.send_message(message.chat.id, rates, reply_markup=main_keyboard())
    else:
        bot.send_message(message.chat.id,
                         "⚠️ Не удалось получить курсы",
                         reply_markup=main_keyboard())


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_handler(message):
    """Обработка кнопки помощи"""
    help_text = (
        "ℹ️ Справка по боту:\n\n"
        "📅 Календарь - выбрать дату\n"
        "🌤 Погода - узнать погоду\n"
        "💬 Цитата - случайная цитата\n"
        "💰 Валюта - курсы USD/EUR\n"
        "❓ Помощь - это сообщение"
    )
    bot.send_message(message.chat.id, help_text, reply_markup=main_keyboard())


@bot.message_handler(func=lambda m: m.text in GROUP_LINKS.keys())
def group_handler(message):
    """Обработка кнопок групп"""
    bot.send_message(message.chat.id,
                     f"Присоединяйтесь: {GROUP_LINKS[message.text]}",
                     disable_web_page_preview=True)


@bot.message_handler(func=lambda m: m.text == "↩️ Назад")
def back_handler(message):
    """Возврат в главное меню"""
    bot.send_message(message.chat.id,
                     "Главное меню:",
                     reply_markup=main_keyboard())


# --- Запуск ---
if __name__ == '__main__':
    print("🟢 Бот успешно запущен")
    bot.infinity_polling()