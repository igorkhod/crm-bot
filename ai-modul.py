import os
import requests
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Загрузка токенов
load_dotenv('token.env')
TOKEN = os.getenv('TOKEN')
DEEPSEEK_API_KEY = os.getenv('IGOR_KHOD_API_KEY')

# Проверка токенов
print("=" * 50)
print(f"🔐 Telegram Token: {TOKEN[:10]}...")
print(f"🔐 DeepSeek Key: {DEEPSEEK_API_KEY[:10]}...")
print("=" * 50)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие с кнопкой"""
    button = KeyboardButton("🔄 Задать вопрос ИИ")
    reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

    await update.message.reply_text(
        "🤖 Я бот с DeepSeek AI. Нажмите кнопку ниже, чтобы задать вопрос:",
        reply_markup=reply_markup
    )


async def handle_ai_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия кнопки и вопросов"""
    if update.message.text == "🔄 Задать вопрос ИИ":
        await update.message.reply_text(
            "📝 Введите ваш вопрос одним сообщением:",
            reply_markup=None  # Убираем клавиатуру на время ввода
        )
        context.user_data['awaiting_question'] = True
    elif context.user_data.get('awaiting_question'):
        # Отправка вопроса в DeepSeek
        question = update.message.text
        try:
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": question}]
            }
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data
            ).json()

            answer = response['choices'][0]['message']['content']
            button = KeyboardButton("🔄 Задать вопрос ИИ")
            reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

            await update.message.reply_text(
                f"🔍 Ответ:\n{answer}",
                reply_markup=reply_markup
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка: {e}")
        finally:
            context.user_data['awaiting_question'] = False
    else:
        button = KeyboardButton("🔄 Задать вопрос ИИ")
        reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
        await update.message.reply_text(
            "Нажмите кнопку, чтобы задать вопрос:",
            reply_markup=reply_markup
        )


def main():
    app = Application.builder().token(TOKEN).build()

    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_request))

    print("🟢 Бот с DeepSeek запущен. Нажмите /start в Telegram.")
    app.run_polling()


if __name__ == "__main__":
    main()