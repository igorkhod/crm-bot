import telebot
from telebot import types

TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"

bot = telebot.TeleBot(TOKEN)



@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Добро пожаловать! Вот что я умею...")


# Обработчик для всех сообщений (если пользователь написал что-то не то)
@bot.message_handler(func=lambda msg: True)
def hint_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('/start')
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=markup
    )


bot.infinity_polling()
