import telebot
from telebot import types

TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"
ADMIN_ID = 448124106  # Ваш реальный ID

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    # Создаем inline-клавиатуру
    markup = types.InlineKeyboardMarkup()

    # Добавляем кнопки меню
    btn1 = types.InlineKeyboardButton("📊 Курсы валют", callback_data="currency")
    btn2 = types.InlineKeyboardButton("🎲 Рандомное число", callback_data="random")
    btn3 = types.InlineKeyboardButton("Открыть сайт", url="https://www.krasnpsytech.ru/")
    btn4 = types.InlineKeyboardButton("ℹ Помощь", callback_data="help")

    markup.row(btn1, btn2)  # Первая строка с 2 кнопками
    markup.row(btn3,btn4) # Вторая строка с 2 кнопками

    # Отправляем сообщение с меню
    bot.send_message(
        message.chat.id,
        "🔍 *Выберите действие:*\n\nМеню:",
        reply_markup=markup,
        parse_mode="Markdown"
    )


# Обработчик нажатий на inline-кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "currency":
        # Ответ на нажатие "Курсы валют"
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "💵 *Курсы валют:*\nUSD: 75.50 RUB\nEUR: 85.30 RUB",
            parse_mode="Markdown"
        )
    elif call.data == "random":
        # Ответ на нажатие "Рандомное число"
        import random
        bot.answer_callback_query(call.id, f"Ваше число: {random.randint(1, 100)}")
    elif call.data == "help":
        # Ответ на нажатие "Помощь"
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "📌 *Помощь:*\nЭто тестовый бот с inline-меню.",
            parse_mode="Markdown"
        )


if __name__ == '__main__':
    print("Бот с inline-меню запущен!")
    bot.polling(none_stop=True)
