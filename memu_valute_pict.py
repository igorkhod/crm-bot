from datetime import datetime
import telebot
from telebot import types
import random
import requests
from xml.etree import ElementTree as ET
import io

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

        elif message.text == '📈 Курсы валют':
            show_currency_menu(message)

        elif message.text in ['🇺🇸 Курс Доллара', '🇪🇺 Курс Евро']:
            currency = "USD" if message.text == '🇺🇸 Курс Доллара' else "EUR"
            rate = get_currency_rate(currency)
            bot.send_message(message.chat.id, rate)

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
            bot.send_message(message.chat.id, 'Главное меню', reply_markup=markup)

        elif message.text == '🧸 Стикер':
            try:
                # 1. Указываем URL стикера
                sticker_url = 'https://psysib.ru/stick.webp'

                # 2. Скачиваем изображение в оперативную память (без сохранения на диск)
                response = requests.get(sticker_url)
                response.raise_for_status()  # Проверка ошибок HTTP

                # 3. Создаем файловый объект в памяти
                sticker_file = io.BytesIO(response.content)
                sticker_file.name = 'sticker.webp'  # Обязательно указываем имя с расширением

                # 4. Отправляем стикер
                bot.send_sticker(message.chat.id, sticker_file)

                # 5. Закрываем файловый объект
                sticker_file.close()

            except requests.exceptions.RequestException:
                bot.send_message(message.chat.id, "⚠️ Не удалось загрузить стикер с сервера")
            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ Ошибка при отправке: {str(e)}")


bot.polling(none_stop=True)

# @bot.message_handler(commands=['date'])
# def send_date(message):
#    current_date = datetime.now().strftime("%d/%m/%Y")
#    url = 'http://www.cbr.ru/scripts/XML_daily.asp?date_req=' + current_date
# bot.infinity_polling()
