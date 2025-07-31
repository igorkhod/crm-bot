import telebot
from telebot import types
import random

TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"  # Для безопасности лучше хранить в переменных окружения
bot = telebot.TeleBot(TOKEN)

# Улучшенное главное меню
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("📊 Основные функции", callback_data="main_functions"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
        types.InlineKeyboardButton("✨ Дополнительно", callback_data="extras")
    ]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_menu(message):
    bot.send_message(
        message.chat.id,
        "🏠 *Главное меню*:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# Обработчики с улучшенной логикой
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        if call.data == "main_functions":
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("📈 Курсы валют", callback_data="currency"),
                types.InlineKeyboardButton("🎲 Рандом 1-100", callback_data="random_num"),
                types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
            )
            bot.edit_message_text(
                "📊 *Доступные функции:*",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="Markdown"
            )

        elif call.data == "currency":
            bot.send_message(
                call.message.chat.id,
                "💱 *Актуальные курсы:*\n"
                "USD → 75.50 RUB\n"
                "EUR → 85.30 RUB\n"
                "CNY → 11.20 RUB",
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id)

        elif call.data == "random_num":
            num = random.randint(1, 100)
            bot.answer_callback_query(
                call.id,
                f"🎯 Ваше число: {num}",
                show_alert=True
            )

        elif call.data == "back_to_main":
            bot.edit_message_text(
                "🔙 Возвращаемся в главное меню...",
                call.message.chat.id,
                call.message.message_id
            )
            send_menu(call.message)

    except Exception as e:
        bot.answer_callback_query(
            call.id,
            "⚠️ Произошла ошибка. Попробуйте позже.",
            show_alert=True
        )
        print(f"Error: {e}")

if __name__ == '__main__':
    print("🔮 Бот успешно запущен!")
    bot.infinity_polling()