from datetime import datetime
import telebot
from telebot import types
import random
import requests
from xml.etree import ElementTree as ET

TOKEN = '8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4'

bot = telebot.TeleBot(TOKEN)


def get_currency_rate(currency_code):
    try:
        current_date = datetime.now().strftime("%d/%m/%Y")
        url = f'http://www.cbr.ru/scripts/XML_daily.asp?date_req={current_date}'

        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        for valute in root.findall('Valute'):
            if valute.find('CharCode').text == currency_code:
                nominal = valute.find('Nominal').text
                value = valute.find('Value').text
                name = valute.find('Name').text
                return f"{nominal} {currency_code} ({name}): {value} руб."

        return f"Курс {currency_code} не найден"
    except Exception as e:
        return f"Ошибка при получении курса: {str(e)}"


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('🔸 Рандомное число')
    item2 = types.KeyboardButton('📈 Курсы валют')
    item3 = types.KeyboardButton('📚 Информация')
    item4 = types.KeyboardButton('➡️ Другое')

    markup.add(item1, item2, item3, item4)

    bot.send_message(message.chat.id, 'Привет, {0.first_name}!'.format(message.from_user), reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '🇺🇸 Курс Доллара')
def handle_usd(message):
    rate = get_currency_rate("USD")
    bot.send_message(message.chat.id, rate)


@bot.message_handler(func=lambda message: message.text == '🇪🇺 Курс Евро')
def handle_eur(message):
    rate = get_currency_rate("EUR")
    bot.send_message(message.chat.id, rate)


@bot.message_handler(func=lambda message: message.text == '📈 Курсы валют')
def show_currency_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('🇺🇸 Курс Доллара')
    item2 = types.KeyboardButton('🇪🇺 Курс Евро')
    back = types.KeyboardButton('⬅️ Назад')
    markup.add(item1, item2, back)
    bot.send_message(message.chat.id, "Выберите валюту для отображения курса:", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def bot_message(message):
    if message.chat.type == 'private':
        if message.text == '🔸 Рандомное число':
            bot.send_message(message.chat.id, 'Ваше число: ' + str(random.randint(0, 1000)))

        elif message.text == '📚 Информация':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('💾 О боте')
            item2 = types.KeyboardButton('📦 Что в коробке?')
            back = types.KeyboardButton('⬅️ Назад')
            markup.add(item1, item2, back)
            bot.send_message(message.chat.id, '📚 Информация', reply_markup=markup)

        elif message.text == '➡️ Другое':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('🛠 Настройки')
            item2 = types.KeyboardButton('✉️ Подписка')
            item3 = types.KeyboardButton('🧸 Стикер')
            back = types.KeyboardButton('⬅️ Назад')
            markup.add(item1, item2, item3, back)
            bot.send_message(message.chat.id, '➡️ Другое', reply_markup=markup)

        elif message.text == '⬅️ Назад':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('🔸 Рандомное число')
            item2 = types.KeyboardButton('📈 Курсы валют')
            item3 = types.KeyboardButton('📚 Информация')
            item4 = types.KeyboardButton('➡️ Другое')
            markup.add(item1, item2, item3, item4)
            bot.send_message(message.chat.id, '⬅️ Назад', reply_markup=markup)

        elif message.text == '🧸 Стикер':
            stick = open('https://psysib.ru/stick.webp', 'rb')
            bot.send_sticker(message.chat.id, stick)


bot.polling(none_stop=True)
