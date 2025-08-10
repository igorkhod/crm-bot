import os
from dotenv import load_dotenv
import telebot
from telebot import types
import time

# Конфигурация (замените значения на свои!)
# Загружаем токен
load_dotenv("token.env")
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверьте файл token.env")
ADMIN_ID = os.getenv("ADMIN_ID")

# Инициализация бота
bot = telebot.TeleBot(TOKEN)


def send_to_admin(message):
    """Отправка уведомлений администратору"""
    try:
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🔔 Уведомление: {message}")
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")


@bot.message_handler(commands=['start'])
def start(message):
    """Главное меню с кнопкой"""
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Меню"))

        bot.send_message(
            message.chat.id,
            "🖐 Привет! Я бот с кнопочным меню.",
            reply_markup=markup
        )

        # Уведомление в ЛС администратора
        send_to_admin(f"Пользователь {message.from_user.id} запустил бота")

    except Exception as e:
        send_to_admin(f"🚨 Ошибка в /start: {e}")


@bot.message_handler(func=lambda m: m.text == "Меню")
def menu(message):
    """Обработчик кнопки меню"""
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("/start"))

        bot.send_message(
            message.chat.id,
            "🔍 Выберите действие:",
            reply_markup=markup
        )
    except Exception as e:
        send_to_admin(f"🚨 Ошибка в меню: {e}")


if __name__ == '__main__':
    try:
        print("✅ Бот запущен. Для остановки: Ctrl+C")
        send_to_admin("🤖 Бот успешно запущен!")
        bot.polling(none_stop=True)

    except Exception as e:
        send_to_admin(f"🔥 Критическая ошибка: {e}")
    finally:
        print("Бот остановлен")