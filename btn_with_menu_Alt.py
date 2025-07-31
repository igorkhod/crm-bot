import telebot
from telebot import types
import os
import sys
import time

TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"


def main():
    try:
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(commands=['start'])
        def start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("Меню"))
            bot.send_message(message.chat.id, "Работаю!", reply_markup=markup)

        @bot.message_handler(func=lambda m: m.text == "Меню")
        def menu(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("/start"))
            bot.send_message(message.chat.id, "Выберите:", reply_markup=markup)

        print("Бот запущен. Ctrl+C для остановки")
        bot.polling(none_stop=True)

    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    # Простой вариант без проверки дубликатов
    main()