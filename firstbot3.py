import telebot
from telebot import types

bot = telebot.TeleBot("8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Получить котика 🐱", callback_data="get_cat")
    markup.add(btn)

    bot.send_message(message.chat.id, "Нажмите кнопку для картинки:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_cat")
def send_cat_image(call):
    bot.send_photo(call.message.chat.id, 'https://psysib.ru/stick.webp')


bot.infinity_polling()
