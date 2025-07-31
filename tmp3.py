import time
import os
from dotenv import load_dotenv
from telebot import TeleBot, types  # Добавили types для кнопок

load_dotenv('token.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = TeleBot(TOKEN)

# Список доступных ИИ
AI_OPTIONS = {
    "gpt": "GPT-4",
    "claude": "Claude 3",
    "llama": "Llama 3"
}

dots = ["•", "●", "●●", "●●●"]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Кнопки выбора ИИ
    markup = types.InlineKeyboardMarkup()
    for ai_id, ai_name in AI_OPTIONS.items():
        markup.add(types.InlineKeyboardButton(ai_name, callback_data=f"ai_{ai_id}"))

    bot.send_message(
        message.chat.id,
        "🤖 Выберите ИИ для обработки запроса:",
        reply_markup=markup
    )


# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith('ai_'))
def handle_ai_selection(call):
    ai_selected = call.data[3:]  # Убираем префикс 'ai_'
    bot.edit_message_text(
        f"Выбран: {AI_OPTIONS[ai_selected]}",
        call.message.chat.id,
        call.message.message_id
    )

    # Сохраняем выбор пользователя (можно использовать глобальный словарь или БД)
    user_id = call.from_user.id
    bot.send_message(
        call.message.chat.id,
        "📝 Теперь отправьте текст для обработки"
    )


@bot.message_handler(func=lambda msg: True)
def process_text(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⏳ Подождите, ИИ обрабатывает запрос")

    # Анимация загрузки
    for frame in dots:
        try:
            bot.edit_message_text(
                f"⏳ Подождите, ИИ обрабатывает запрос {frame}",
                chat_id,
                msg.message_id
            )
            time.sleep(0.5)
        except:
            pass

    # Здесь должна быть реальная обработка через выбранный ИИ
    time.sleep(2)
    bot.edit_message_text(
        f"✅ Готово! Результат:\n{message.text} (обработано {AI_OPTIONS.get('gpt', 'GPT-4')})",
        chat_id,
        msg.message_id
    )


if __name__ == '__main__':
    bot.polling()