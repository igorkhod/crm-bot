import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from dotenv import load_dotenv
import os

# Загружаем переменные из файла .env
load_dotenv('token.env')  # Файл с токеном в формате TOKEN=ваш_токен

# Создаем экземпляр бота
TOKEN = os.getenv("TOKEN")  # Получаем токен из переменных окружения
bot = telebot.TeleBot(TOKEN)  # Инициализируем бота


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(m):
    """Обработка команды /start с созданием интерактивного календаря"""
    # Создаем календарь
    calendar, step = DetailedTelegramCalendar().build()

    # Отправляем сообщение с календарем
    bot.send_message(
        chat_id=m.chat.id,  # ID чата
        text=f"Выберите {LSTEP[step]}",  # Текст с указанием выбора (день/месяц/год)
        reply_markup=calendar  # Прикрепляем календарь как клавиатуру
    )


# Обработчик callback-запросов от календаря
@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(c):
    """Обработка взаимодействия с календарем"""
    # Обрабатываем данные календаря
    result, key, step = DetailedTelegramCalendar().process(c.data)

    if not result and key:
        # Если дата не выбрана полностью (только год или месяц)
        bot.edit_message_text(
            chat_id=c.message.chat.id,  # ID чата
            message_id=c.message.message_id,  # ID сообщения для редактирования
            text=f"Выберите {LSTEP[step]}",  # Обновляем текст
            reply_markup=key  # Обновляем клавиатуру
        )
    elif result:
        # Когда дата полностью выбрана
        bot.edit_message_text(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            text=f"Вы выбрали дату: {result.strftime('%d.%m.%Y')}",  # Форматируем дату
        )


# Обработчик для создания кнопок
@bot.message_handler(commands=['menu'])
def show_menu(message):
    """Создание меню с кнопками"""
    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    # Создаем кнопки
    btn1 = types.KeyboardButton('Календарь 📅')
    btn2 = types.KeyboardButton('Цитата 💬')
    btn3 = types.KeyboardButton('Помощь ℹ️')

    # Добавляем кнопки в клавиатуру
    markup.add(btn1, btn2, btn3)

    # Отправляем сообщение с клавиатурой
    bot.send_message(
        chat_id=message.chat.id,
        text="Выберите действие:",
        reply_markup=markup
    )


# Обработчик текстовых сообщений (для кнопок)
@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработка нажатий на кнопки"""
    if message.text == 'Календарь 📅':
        # При нажатии на кнопку календаря
        calendar, step = DetailedTelegramCalendar().build()
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Выберите {LSTEP[step]}",
            reply_markup=calendar
        )
    elif message.text == 'Цитата 💬':
        # При нажатии на кнопку цитаты
        bot.send_message(
            chat_id=message.chat.id,
            text="Здесь будет случайная цитата"
        )
    elif message.text == 'Помощь ℹ️':
        # При нажатии на кнопку помощи
        bot.send_message(
            chat_id=message.chat.id,
            text="Это бот с календарем и цитатами.\n\n"
                 "Доступные команды:\n"
                 "/start - Открыть календарь\n"
                 "/menu - Показать меню с кнопками"
        )


# Запускаем бота в режиме нон-стоп
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True, interval=0)  # interval=0 для максимальной отзывчивости