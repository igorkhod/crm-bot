import os
import requests
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont
import logging

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")

# Конфигурация
CITIES = {
    "Красноярск": {"code": "Krasnoyarsk", "emoji": "🏙️"},
    "Иркутск": {"code": "Irkutsk", "emoji": "🏔️"}
}

QUOTES = [
    "Счастье - это не что-то готовое. Оно зависит от ваших действий. — Далай-лама",
    "Единственный способ сделать великую работу — любить то, что вы делаете. — Стив Джобс",
    "Ваше время ограничено, не тратьте его, живя чужой жизнью. — Стив Джобс"
]

PSYCHO_NET_GROUPS = [
    {"name": "Психонет Основной", "url": "https://t.me/psycho_net_main"},
    {"name": "Психонет Поддержка", "url": "https://t.me/psycho_net_support"}
]


async def generate_weather_image(city: str, weather_data: dict):
    """Генерация изображения с погодой"""
    try:
        img = Image.new('RGB', (800, 400), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)

        try:
            with Image.open(f"images/{CITIES[city]['code']}.jpg") as city_img:
                city_img = city_img.resize((400, 400))
                img.paste(city_img, (0, 0))
        except Exception as e:
            logger.warning(f"Не найдено изображение города: {e}")
            draw.rectangle([0, 0, 400, 400], fill="#3498db")
            try:
                font = ImageFont.truetype("arial.ttf", 30)
            except:
                font = ImageFont.load_default()
            draw.text((100, 180), f"{CITIES[city]['emoji']} {city}", fill="white", font=font)

        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()

        weather_text = f"""{CITIES[city]['emoji']} Погода в {city}
🌡️ {weather_data['temp']}°C (ощущается {weather_data['feels_like']}°C)
☀️ {weather_data['description']}
🌬️ Ветер: {weather_data['wind_speed']} м/с
💧 Влажность: {weather_data['humidity']}%
🕒 {weather_data['time']}"""

        draw.text((420, 50), weather_text, fill="black", font=font)
        img.save("weather_card.jpg")
        return True
    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {e}")
        return False


async def get_weather_data(city: str):
    """Получение данных о погоде"""
    try:
        city_code = CITIES.get(city, {}).get('code', city)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_code}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            'temp': int(data["main"]["temp"]),
            'feels_like': int(data["main"]["feels_like"]),
            'description': data["weather"][0]["description"],
            'wind_speed': data["wind"]["speed"],
            'humidity': data["main"]["humidity"],
            'time': datetime.now().strftime("%H:%M")
        }
    except Exception as e:
        logger.error(f"Ошибка запроса погоды: {e}")
        return None


async def get_exchange_rates():
    """Получение курсов валют с улучшенной обработкой ошибок"""
    try:
        url = f"https://openexchangerates.org/api/latest.json?app_id={EXCHANGE_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data.get('rates'), dict):
            raise ValueError("Invalid rates data in response")

        rub_rate = data['rates'].get('RUB')
        eur_rate = data['rates'].get('EUR')

        if not all([rub_rate, eur_rate]):
            raise ValueError("Missing required currency rates")

        return {
            'USD': rub_rate,
            'EUR': rub_rate / eur_rate
        }
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")
        return {'USD': 75.0, 'EUR': 85.0}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("🌤 Погода", callback_data='weather')],
        [InlineKeyboardButton("📅 Календарь", callback_data='calendar')],
        [InlineKeyboardButton("💰 Валюта", callback_data='currency')],
        [InlineKeyboardButton("💬 Цитата", callback_data='quote')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')],
        [InlineKeyboardButton(PSYCHO_NET_GROUPS[0]['name'], url=PSYCHO_NET_GROUPS[0]['url'])],
        [InlineKeyboardButton(PSYCHO_NET_GROUPS[1]['name'], url=PSYCHO_NET_GROUPS[1]['url'])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if update.message:
            await update.message.reply_text(
                "🔮 Добро пожаловать в психо-ассистент!\n"
                "Выберите нужную функцию:",
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text="🔮 Добро пожаловать в психо-ассистент!\nВыберите нужную функцию:",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок"""
    try:
        query = update.callback_query
        await query.answer()

        if query.data == 'weather':
            await weather_menu(query, context)
        elif query.data == 'calendar':
            await calendar(query, context)
        elif query.data == 'currency':
            await currency(query, context)
        elif query.data == 'quote':
            await quote(query, context)
        elif query.data == 'help':
            await help_command(query, context)
        elif query.data.startswith('city_'):
            city = query.data[5:]
            await send_weather(query, city, context)
        elif query.data == 'back':
            await start(update, context)
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")


async def weather_menu(query, context: ContextTypes.DEFAULT_TYPE):
    """Меню выбора города для погоды"""
    try:
        keyboard = [[InlineKeyboardButton(f"{data['emoji']} {city}", callback_data=f'city_{city}')]
                    for city, data in CITIES.items()]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])

        await query.edit_message_text(
            text="🌤 Выберите город для просмотра погоды:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Ошибка в меню погоды: {e}")


async def send_weather(query, city, context: ContextTypes.DEFAULT_TYPE):
    """Отправка информации о погоде"""
    try:
        weather_data = await get_weather_data(city)
        if not weather_data:
            await query.edit_message_text("Не удалось получить данные о погоде. Попробуйте позже.")
            return

        if await generate_weather_image(city, weather_data):
            try:
                with open("weather_card.jpg", "rb") as photo:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=photo,
                        caption=f"{CITIES[city]['emoji']} Погода в {city} на {weather_data['time']}"
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}")
                await query.edit_message_text("Ошибка при отправке изображения погоды")
        else:
            await query.edit_message_text(
                f"{CITIES[city]['emoji']} Погода в {city}:\n"
                f"🌡️ {weather_data['temp']}°C (ощущается {weather_data['feels_like']}°C)\n"
                f"☀️ {weather_data['description']}\n"
                f"🌬️ Ветер: {weather_data['wind_speed']} м/с\n"
                f"💧 Влажность: {weather_data['humidity']}%\n"
                f"🕒 Обновлено: {weather_data['time']}"
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке погоды: {e}")


async def calendar(query, context: ContextTypes.DEFAULT_TYPE):
    """Отображение календаря"""
    try:
        now = datetime.now()
        await query.edit_message_text(
            f"📅 Календарь:\n"
            f"Сегодня: {now.strftime('%d.%m.%Y')}\n"
            f"День недели: {now.strftime('%A')}\n"
            f"Время: {now.strftime('%H:%M')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='back')]])
        )
    except Exception as e:
        logger.error(f"Ошибка в календаре: {e}")


async def currency(query, context: ContextTypes.DEFAULT_TYPE):
    """Отображение курсов валют"""
    try:
        rates = await get_exchange_rates()
        await query.edit_message_text(
            f"💰 Курсы валют:\n"
            f"1 USD = {rates['USD']:.2f} RUB\n"
            f"1 EUR = {rates['EUR']:.2f} RUB\n"
            f"Обновлено: {datetime.now().strftime('%H:%M')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='back')]])
        )
    except Exception as e:
        logger.error(f"Ошибка в курсах валют: {e}")
        await query.edit_message_text("Не удалось получить курсы валют. Попробуйте позже.")


async def quote(query, context: ContextTypes.DEFAULT_TYPE):
    """Отображение случайной цитаты"""
    try:
        await query.edit_message_text(
            f"💬 Цитата дня:\n{random.choice(QUOTES)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='back')]])
        )
    except Exception as e:
        logger.error(f"Ошибка в цитате: {e}")


async def help_command(query, context: ContextTypes.DEFAULT_TYPE):
    """Помощь по боту"""
    try:
        await query.edit_message_text(
            "ℹ️ Помощь:\n"
            "Этот бот предоставляет:\n"
            "- Текущую погоду в выбранном городе\n"
            "- Актуальные курсы валют\n"
            "- Календарь и текущее время\n"
            "- Вдохновляющие цитаты\n\n"
            "Просто выберите нужную функцию в меню!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='back')]])
        )
    except Exception as e:
        logger.error(f"Ошибка в помощи: {e}")


def main():
    """Запуск бота"""
    try:
        app = Application.builder().token(TOKEN).build()

        # Регистрация обработчиков
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))

        logger.info("Бот запущен и ожидает сообщений...")
        app.run_polling()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")


if __name__ == "__main__":
    main()