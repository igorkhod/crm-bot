
import os
from dotenv import load_dotenv
import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
# Загружаем токен
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверьте файл token.env")


bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(m.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    result, key, step = DetailedTelegramCalendar().process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected {result}",
                              c.message.chat.id,
                              c.message.message_id)

bot.polling(none_stop=True)