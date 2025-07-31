"""
This is the simplest example of how to use several calendars in one.
This example is not realistic, but imagine that you need 2 calendars: one russian and one english.

It can be used with different date ranges, for example when you need calendar for specifying a person's birth date
and another one for specifying booking date. These two have different properties and hence need to be handled
differently.
"""
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


# @bot.message_handler(commands=['start1'])
# def start1(m):
#     # do not forget to put calendar_id
#     calendar, step = DetailedTelegramCalendar(calendar_id=1).build()
#     bot.send_message(m.chat.id,
#                      f"Calendar 1: Select {LSTEP[step]}",
#                      reply_markup=calendar)


@bot.message_handler(commands=['start'])
def start(m):
    # do not forget to put calendar_id
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    bot.send_message(
        m.chat.id,
        f"Календарь: Выборите год",
        # f"Календарь 2: Выбор  {LSTEP[step]}",
        reply_markup=calendar
    )


#
# @bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
# def cal1(c):
#     # calendar_id is used here too, since the new keyboard is made
#     result, key, step = DetailedTelegramCalendar(calendar_id=1).process(c.data)
#     if not result and key:
#         bot.edit_message_text(f"Calendar 1: Select {LSTEP[step]}",
#                               c.message.chat.id,
#                               c.message.message_id,
#                               reply_markup=key)
#     elif result:
#         bot.edit_message_text(f"You selected {result} in calendar 1",
#                               c.message.chat.id,
#                               c.message.message_id)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal1(c):
    # calendar_id is used here too, since the new keyboard is made
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(c.data)
    if not result and key:
        bot.edit_message_text(
            f"Календарь 2: Выберите {LSTEP[step]}",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=key)
    elif result:
        bot.edit_message_text(f"Вы выбрали дату {result} в календаре ",
                              c.message.chat.id,
                              c.message.message_id)


bot.polling()
