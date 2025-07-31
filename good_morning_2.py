import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime  # Импортируем модуль для работы с датой

# --- Загрузка токена ---
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверьте файл token.env")

# --- Клавиатура ---
KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Доброе утро! 🌞", "Спокойной ночи! 🌙"],
        ["Мотивация 💪", "Котик 🐱"],
        ["Психонетика Инь-Ян", "Иркутск психотехнологии"]
    ],
    resize_keyboard=True
)


# --- Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем текущую дату и день недели
    today = datetime.now()

    # Словари для перевода
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    weekdays = {
        0: "понедельник", 1: "вторник", 2: "среда",
        3: "четверг", 4: "пятница", 5: "суббота", 6: "воскресенье"
    }


    date_str = f"сегодня {today.day} {months[today.month]} {today.year} года, {weekdays[today.weekday()]}"
  # Форматируем дату

    await update.message.reply_text(
        f"{date_str}\n\nВыберите действие:",
        reply_markup=KEYBOARD
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 Доступные команды:\n"
        "/start - показать кнопки\n"
        "/help - эта справка\n\n"
        "Или нажмите одну из кнопок ниже!"
    )
    await update.message.reply_text(help_text, reply_markup=KEYBOARD)


# --- Обработчик кнопок ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    responses = {
        "Доброе утро! 🌞": "И вам доброго утра! ☀️ Пусть сегодня будет продуктивный день!",
        "Спокойной ночи! 🌙": "Спокойной ночи! 🌜 Пусть сны будут волшебными!",
        "Мотивация 💪": "Ты можешь больше, чем думаешь! Сегодня – твой день! 🚀",
        "Котик 🐱": "https://cataas.com/cat",  # Ссылка на случайного котика
        "Психонетика Инь-Ян": "https://t.me/+EL9esd0xZ-xkMTU6",
        "Иркутск психотехнологии": "https://t.me/+7ZBrobhAJoRhM2U6"
    }

    if text in responses:
        if "Котик" in text:
            await update.message.reply_photo(responses[text])
        else:
            await update.message.reply_text(responses[text])


# --- Запуск бота ---
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🟢 Бот запущен. Отправьте /start в Telegram")
    app.run_polling()
