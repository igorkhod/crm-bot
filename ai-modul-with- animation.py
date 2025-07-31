import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Message
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    button = KeyboardButton("🔄 Задать вопрос ИИ")
    reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
    await update.message.reply_text(
        "🤖 Я бот с DeepSeek AI. Нажмите кнопку для вопроса:",
        reply_markup=reply_markup
    )


async def show_typing_animation(update: Update) -> Message:
    """Анимация точек через редактирование сообщения"""
    dots = ["", ".", "..", "..."]
    message = await update.message.reply_text("🤖 Думаю")

    for i in range(12):  # 12 итераций × 0.5 сек = 6 сек максимально
        await asyncio.sleep(0.5)
        try:
            await message.edit_text(f"🤖 Думаю{dots[i % 4]}")
        except:
            break
    return message


async def handle_ai_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == "🔄 Задать вопрос ИИ":
        await update.message.reply_text(
            "📝 Введите ваш вопрос:",
            reply_markup=None
        )
        context.user_data['awaiting_question'] = True
        return

    if not context.user_data.get('awaiting_question'):
        button = KeyboardButton("🔄 Задать вопрос ИИ")
        reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
        await update.message.reply_text(
            "Нажмите кнопку для вопроса:",
            reply_markup=reply_markup
        )
        return

    question = update.message.text

    # Запускаем анимацию
    animation_task = asyncio.create_task(show_typing_animation(update))

    try:
        # Делаем запрос к API
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.7
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        ).json()

        answer = response['choices'][0]['message']['content']

        # Останавливаем анимацию
        animation_task.cancel()

        # Удаляем анимационное сообщение
        if not animation_task.done():
            await (await animation_task).delete()

        # Отправляем ответ
        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)}")
    finally:
        # Возвращаем кнопку
        button = KeyboardButton("🔄 Задать вопрос ИИ")
        reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
        await update.message.reply_text(
            "Готов к новым вопросам!",
            reply_markup=reply_markup
        )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_request))
    print("🟢 Бот запущен. Нажмите /start в Telegram.")
    app.run_polling()


if __name__ == "__main__":
    main()