import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем токен
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверьте файл token.env")

# Создаем клавиатуру с одной кнопкой
KEYBOARD = ReplyKeyboardMarkup([["Доброе утро! 🌞"]], resize_keyboard=True)


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы получить приветствие:",
        reply_markup=KEYBOARD
    )


# Обработчик нажатия кнопки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Доброе утро! 🌞":
        await update.message.reply_text("И вам доброго утра! ☀️ Пусть день будет прекрасным!")


# Запуск бота
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🟢 Бот запущен. Отправьте /start в Telegram")
    app.run_polling()