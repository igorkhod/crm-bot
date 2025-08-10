import os
from dotenv import load_dotenv

# Загружаем токен
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверьте файл token.env")

from telebot import TeleBot

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

bot = TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    bot.send_message(m.chat.id,
                     f"Календарь 2: Выборите год",
                     reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal1(c):
    # calendar_id is used here too, since the new keyboard is made
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(c.data)
    if not result and key:
        bot.edit_message_text(f"Календарь 2: Выберите {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Вы выбрали дату {result} в календаре ",
                              c.message.chat.id,
                              c.message.message_id)


bot.polling()