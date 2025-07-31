from datetime import datetime
import telebot
from telebot import types
import threading
import time

TOKEN = '8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4'
bot = telebot.TeleBot(TOKEN)

# Список для хранения chat_id пользователей
users_subscribed = set()


@bot.message_handler(commands=['start'])
def start(message):
    # Добавляем пользователя в список подписчиков
    users_subscribed.add(message.chat.id)

    # Создаем клавиатуру с /start в строке сообщений
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = types.KeyboardButton('/start')
    markup.add(btn_start)

    # Приветственное сообщение
    bot.send_message(
        message.chat.id,
        f'Привет, {message.from_user.first_name}! Я буду желать тебе доброго утра! ☀️\n\n'
        'Каждое утро в 7:00 я буду присылать тебе приятное сообщение!',
        reply_markup=markup
    )


def send_morning_notification():
    while True:
        now = datetime.now()
        if now.hour == 7 and now.minute == 0:  # 7:00 утра
            for user_id in users_subscribed:
                try:
                    # Создаем клавиатуру с /start
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn_start = types.KeyboardButton('/start')
                    markup.add(btn_start)

                    # Отправляем утреннее сообщение
                    bot.send_message(
                        user_id,
                        f'☀️ Доброе утро, дружище!\n'
                        f'Сегодня {now.strftime("%d.%m.%Y")}\n'
                        f'Пусть день будет продуктивным! 💪',
                        reply_markup=markup
                    )

                    # Можно добавить стикер
                    bot.send_sticker(user_id, 'https://psysib.ru/stick.webp')

                except Exception as e:
                    print(f"Ошибка отправки уведомления: {e}")
            time.sleep(60)  # Проверяем каждую минуту
        time.sleep(30)  # Проверка времени каждые 30 секунд


# Запускаем уведомления в отдельном потоке
notification_thread = threading.Thread(target=send_morning_notification)
notification_thread.daemon = True
notification_thread.start()


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text == '/start':
        start(message)


bot.polling(none_stop=True)