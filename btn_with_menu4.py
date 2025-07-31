import telebot
from telebot import types
import random

TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"
bot = telebot.TeleBot(TOKEN)

# Главное меню
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📊 Основные функции", callback_data="main_functions"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
    )
    markup.row(
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
        types.InlineKeyboardButton("🎁 Дополнительно", callback_data="extras")
    )
    return markup

# Меню "Основные функции"
def functions_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📈 Курсы валют", callback_data="currency"),
        types.InlineKeyboardButton("🔢 Рандомное число", callback_data="random_num")
    )
    markup.row(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    return markup

# Меню "Настройки"
def settings_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔔 Уведомления", callback_data="notifications"),
        types.InlineKeyboardButton("🌐 Язык", callback_data="language")
    )
    markup.row(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🏠 *Главное меню*:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# Обработчик нажатий на inline-кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == "main_functions":
            bot.edit_message_text(
                "📊 *Основные функции*:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=functions_menu(),
                parse_mode="Markdown"
            )

        elif call.data == "settings":
            bot.edit_message_text(
                "⚙️ *Настройки*:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=settings_menu(),
                parse_mode="Markdown"
            )

        elif call.data == "back_to_main":
            bot.edit_message_text(
                "🏠 *Главное меню*:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=main_menu(),
                parse_mode="Markdown"
            )

        elif call.data == "currency":
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "💵 *Курсы валют*:\nUSD: 75.50 RUB\nEUR: 85.30 RUB",
                parse_mode="Markdown"
            )

        elif call.data == "random_num":
            bot.answer_callback_query(
                call.id,
                f"🎲 Ваше число: {random.randint(1, 100)}",
                show_alert=True
            )

        elif call.data == "help":
            bot.edit_message_text(
                "ℹ️ *Помощь*:\nЭто демонстрация многоуровневого меню.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )

        # Добавлен обработчик для "extras"
        elif call.data == "extras":
            bot.edit_message_text(
                "🎁 *Дополнительные функции*:\nЗдесь могут быть ваши дополнительные функции",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    print("Бот с многоуровневым меню запущен!")
    bot.polling(none_stop=True)