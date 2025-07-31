import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import logging
from datetime import datetime

# Настройка логгирования
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)

# Загрузка конфигурации
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Словарь городов
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


async def generate_weather_image(city: str, weather_data: dict):
    """Генерация изображения с погодой"""
    try:
        img = Image.new('RGB', (800, 400), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)

        # Левая часть - изображение города
        try:
            city_img = Image.open(f"images/{CITIES[city]['code']}.jpg")
            city_img = city_img.resize((400, 400))
            img.paste(city_img, (0, 0))
        except Exception as e:
            #            logger.warning(f"Не найдено изображение города: {e}")
            draw.rectangle([0, 0, 400, 400], fill="#3498db")
            try:
                font = ImageFont.truetype("arial.ttf", 30)
            except:
                font = ImageFont.load_default()
            draw.text((100, 180), f"{CITIES[city]['emoji']} {city}", fill="white", font=font)

        # Правая часть - информация о погоде
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
        #        logger.error(f"Ошибка генерации изображения: {e}")
        return False


async def get_weather_data(city: str):
    """Получение данных о погоде"""
    try:
        city_code = CITIES.get(city, {}).get('code', city)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_code}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url).json()

        return {
            'temp': int(response["main"]["temp"]),
            'feels_like': int(response["main"]["feels_like"]),
            'description': response["weather"][0]["description"],
            'wind_speed': response["wind"]["speed"],
            'humidity': response["main"]["humidity"],
            'time': datetime.now().strftime("%H:%M")
        }
    except Exception as e:
        #        logger.error(f"Ошибка запроса погоды: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    cities_list = "\n".join([f"{data['emoji']} {name}" for name, data in CITIES.items()])
    await update.message.reply_text(
        f"🌤️ Привет! Я бот погоды.\n"
        f"Доступные города:\n{cities_list}\n\n"
        "Отправь /weather [город] для получения информации\n"
        "Например: /weather Красноярск"
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /weather"""
    city = " ".join(context.args) if context.args else "Красноярск"

    if city not in CITIES:
        await update.message.reply_text("Этот город не поддерживается. Доступные города:\n" +
                                        "\n".join(CITIES.keys()))
        return

    #    logger.info(f"Запрос погоды для города: {city}")

    weather_data = await get_weather_data(city)
    if not weather_data:
        await update.message.reply_text("Не удалось получить данные о погоде. Попробуйте позже.")
        return

    if await generate_weather_image(city, weather_data):
        with open("weather_card.jpg", "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"{CITIES[city]['emoji']} Погода в {city} на {weather_data['time']}"
            )
    else:
        await update.message.reply_text(
            f"{CITIES[city]['emoji']} Погода в {city}:\n"
            f"🌡️ {weather_data['temp']}°C (ощущается {weather_data['feels_like']}°C)\n"
            f"☀️ {weather_data['description']}\n"
            f"🌬️ Ветер: {weather_data['wind_speed']} м/с\n"
            f"💧 Влажность: {weather_data['humidity']}%\n"
            f"🕒 Обновлено: {weather_data['time']}"
        )


def main():
    """Запуск бота"""
    try:
        app = Application.builder().token(TOKEN).build()

        # Регистрация обработчиков команд
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("weather", weather))

        #        logger.info("Бот запущен и ожидает сообщений...")
        app.run_polling()
#    except Exception as e:


#       logger.error(f"Ошибка запуска бота: {e}")


if __name__ == "__main__":
    main()
