import telebot
from telebot import types
import time

TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"
ADMIN_ID = 448124106  # Ваш реальный ID

bot = telebot.TeleBot(TOKEN)


def send_to_admin(context, user_id=ADMIN_ID):
    """
    Улучшенная функция уведомлений
    :param context: текст сообщения (str) или объект message
    :param user_id: опционально, ID пользователя
    """
    try:
        if not ADMIN_ID:
            return

        # Определяем ID пользователя
        actual_user_id = None
        if hasattr(context, 'from_user'):
            actual_user_id = str(context.from_user.id)
        elif user_id:
            actual_user_id = str(user_id)

        # Не отправляем уведомления о себе
        if actual_user_id and actual_user_id == str(ADMIN_ID):
            return

        # Формируем текст сообщения
        if isinstance(context, str):
            text = context
        else:
            text = f"👤 Действие от пользователя: {actual_user_id or 'N/A'}\n" \
                   f"🕒 Время: {time.strftime('%Y-%m-%d %H:%M:%S')}\n" \
                   f"✉ Контент: {getattr(context, 'text', 'Нет текста')}"

        bot.send_message(ADMIN_ID, f"🔔 Уведомление:\n{text}")

    except Exception as e:
        print(f"⚠ Ошибка в send_to_admin: {e}")


@bot.message_handler(commands=['start'])
def start(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Меню"))

        bot.send_message(
            message.chat.id,

            "Привет! Я бот с уведомлениями.",
            reply_markup=markup
        )

        # Теперь передаем message объект
        send_to_admin(message)

    except Exception as e:
        send_to_admin(f"Ошибка в /start: {str(e)}")


@bot.message_handler(func=lambda m: m.text == "Меню")
def menu(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("/start"))

        bot.send_message(
            message.chat.id,
            "Выберите действие:",
            reply_markup=markup
        )
    except Exception as e:
        send_to_admin(f"Ошибка в меню: {str(e)}")


if __name__ == '__main__':
    try:
        print("Бот запущен!")
        # Для системных сообщений передаем текст и None как user_id
        send_to_admin("Для начала работы нажми /start", user_id=None)
        # send_to_admin("Бот успешно запущен", user_id=None)
        bot.polling(none_stop=True)
    except Exception as e:
        send_to_admin(f"Критическая ошибка: {str(e)}")
