import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

# --- 1. Инициализация ---
load_dotenv("token.env")

# Распечатка ключей (первые 5 символов)
print("\n" + "=" * 50)
print("АКТИВНЫЕ КЛЮЧИ:")
print(f"TELEGRAM: {os.getenv('TELEGRAM_TOKEN')[:5]}...")
print(f"DEEPSEEK: {os.getenv('IGOR_KHOD_DEEPSEEK_API_KEY')[:5]}...")
print(f"OPENAI: {os.getenv('IGOR_OPENAI_API')[:5]}...")
print("=" * 50 + "\n")

# --- 2. Настройка логов ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 3. Инициализация API ---
clients = {
    "deepseek": OpenAI(
        api_key=os.environ['IGOR_KHOD_DEEPSEEK_API_KEY'],
        base_url="https://api.deepseek.com/v1"
    ),
    "openai": OpenAI(api_key=os.environ['IGOR_OPENAI_API'])
}

# --- 4. Конфигурация моделей ---
MODELS = {
    "deepseek": {
        "name": "DeepSeek-V3",
        "client": "deepseek",
        "model_name": "deepseek-chat",
        "description": "🔹 Модель: DeepSeek-V3\n• Контекст: 128K токенов\n• Актуальность: июль 2024",
        "fallback": None,
        "identity_prompt": "Ты - DeepSeek-V3. Никогда не говори что ты GPT. Всегда явно указывай что ты DeepSeek-V3. Вот твои характеристики:\n- Разработчик: DeepSeek\n- Контекст: 128K токенов\n- Поддержка файлов: PDF, Word, Excel"
    },
    "gpt-4": {
        "name": "GPT-4 Turbo",
        "client": "openai",
        "model_name": "gpt-4-turbo-preview",
        "description": "🔹 Модель: GPT-4 Turbo (OpenAI)\n• Версия: turbo\n• Актуальность: июнь 2024",
        "fallback": "deepseek",
        "identity_prompt": "Ты - GPT-4 Turbo от OpenAI. Никогда не говори что ты DeepSeek. Всегда явно указывай что ты GPT-4 Turbo. Вот твои характеристики:\n- Разработчик: OpenAI\n- Версия: turbo\n- Максимальный контекст: 128K токенов"
    },
    "gpt-3.5": {
        "name": "GPT-3.5",
        "client": "openai",
        "model_name": "gpt-3.5-turbo",
        "description": "🔹 Модель: GPT-3.5 (OpenAI)\n• Базовая версия\n• Актуальность: 2023",
        "fallback": "deepseek",
        "identity_prompt": "Ты - GPT-3.5 от OpenAI. Никогда не говори что ты DeepSeek. Всегда явно указывай что ты GPT-3.5. Вот твои характеристики:\n- Разработчик: OpenAI\n- Версия: 3.5\n- Максимальный контекст: 16K токенов"
    }
}

# --- 5. Глобальные переменные ---
user_sessions = {}
DOTS_ANIMATION = ["•", "●", "••", "•••"]  # Анимация загрузки


# --- 6. Основные функции ---
async def get_model_response(model_id: str, prompt: str) -> str:
    """Получает ответ с жесткой привязкой идентичности модели"""
    model = MODELS[model_id]

    # Логируем запрос
    logger.info(f"Запрос к {model_id} | Пользователь: {prompt[:50]}...")

    try:
        response = clients[model["client"]].chat.completions.create(
            model=model["model_name"],
            messages=[
                {"role": "system", "content": model["identity_prompt"]},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7
        )
        answer = response.choices[0].message.content

        # Проверка идентичности в ответе
        required_keywords = {
            "deepseek": ["DeepSeek", "deepseek"],
            "gpt-4": ["GPT-4", "OpenAI"],
            "gpt-3.5": ["GPT-3.5", "OpenAI"]
        }

        if not any(kw in answer for kw in required_keywords[model_id]):
            answer = f"{model['name']}:\n{answer}"

        return answer

    except Exception as e:
        logger.error(f"Ошибка {model_id}: {str(e)}")
        if model["fallback"]:
            return await get_model_response(model["fallback"], prompt)
        raise


async def animate_typing(update, context, message_id, model_name):
    """Анимация загрузки с точками"""
    for i in range(len(DOTS_ANIMATION) * 2):  # 2 полных цикла
        try:
            await context.bot.edit_message_text(
                f"⏳ {model_name} думает {DOTS_ANIMATION[i % len(DOTS_ANIMATION)]}",
                chat_id=update.message.chat_id,
                message_id=message_id
            )
            await asyncio.sleep(0.5)
        except:
            break


# --- 7. Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start с кнопками"""
    keyboard = [
        [InlineKeyboardButton(model["name"], callback_data=model_id)]
        for model_id, model in MODELS.items()
    ]
    await update.message.reply_text(
        "🤖 Выберите модель ИИ:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора модели"""
    query = update.callback_query
    model_id = query.data
    user_sessions[query.from_user.id] = model_id

    # Логируем выбор модели
    logger.info(f"Пользователь {query.from_user.id} выбрал {model_id}")

    await query.edit_message_text(
        f"✅ {MODELS[model_id]['description']}\n\n"
        "Отправьте ваш запрос..."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений"""
    user = update.effective_user
    user_id = user.id

    if user_id not in user_sessions:
        await start(update, context)
        return

    model_id = user_sessions[user_id]
    model = MODELS[model_id]
    processing_msg = await update.message.reply_text(f"⏳ {model['name']} думает...")

    # Запуск анимации
    animation_task = asyncio.create_task(
        animate_typing(update, context, processing_msg.message_id, model['name'])
    )

    try:
        response = await get_model_response(model_id, update.message.text)
        animation_task.cancel()

        # Форматированный ответ с гарантией указания модели
        formatted_response = (
            f"🤖 *{model['name']}* отвечает:\n\n"
            f"{response}\n\n"
            f"_{model['description'].split('\n')[0]}_"
        )

        await context.bot.edit_message_text(
            formatted_response,
            chat_id=update.message.chat_id,
            message_id=processing_msg.message_id,
            parse_mode="Markdown"
        )

        # Логируем успешный ответ
        logger.info(f"Ответ {model_id} пользователю {user_id}")

    except Exception as e:
        error_msg = f"⚠️ Ошибка: {str(e)}"
        await context.bot.edit_message_text(
            error_msg,
            chat_id=update.message.chat_id,
            message_id=processing_msg.message_id
        )
        logger.error(f"Ошибка у {user_id}: {error_msg}")


# --- 8. Запуск ---
def main():
    # Проверка файла логов
    if not os.path.exists("bot.log"):
        with open("bot.log", "w") as f:
            f.write("Лог бота\n" + "=" * 50 + "\n")

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен и готов к работе!")
    app.run_polling()


if __name__ == "__main__":
    main()