import telebot
from telebot import types

# Сначала создаём объект бота
TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"  # Замените на реальный токен!
bot = telebot.TeleBot(TOKEN)  # Объявление переменной bot


@bot.message_handler(commands=['start'])
def start(message):
    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('/start')
    markup.add(btn)

    # Отправляем сообщение с кнопкой
    bot.send_message(
        chat_id=message.chat.id,  # Используем message.chat.id
        text="Нажмите кнопку, чтобы начать:",
        reply_markup=markup
    )


bot.infinity_polling()
