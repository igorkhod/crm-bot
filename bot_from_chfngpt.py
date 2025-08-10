import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv("token.env")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("IGOR_OPENAI_API")

# --- Настройки ---
# TELEGRAM_BOT_TOKEN = "ВАШ_ТОКЕН_ТЕЛЕГРАМ"
# OPENAI_API_KEY = "ВАШ_ТОКЕН_OPENAI"

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши мне что-нибудь – я спрошу ChatGPT.")

async def chatgpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Запрос к ChatGPT
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты умный помощник, отвечай кратко и понятно."},
            {"role": "user", "content": user_text},
        ]
    )

    answer = completion.choices[0].message.content
    await update.message.reply_text(answer)

# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_reply))

    app.run_polling()

if __name__ == "__main__":
    main()
