import telebot
from pyexpat.errors import messages
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random

bot = telebot.TeleBot("8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4")

@bot.message_handler(commands=['утро'])
def good_morning(message):
    morning_sticker = 'https://psysib.ru/stick.webp'  # или ссылка на утренний стикер
    bot.send_sticker(message.chat.id, morning_sticker)
    bot.send_message(message.chat.id, f'Доброе утро, {message.from_user.first_name}! 🌞')

@bot.message_handler(commands=['start'])
def send_welcome(message_start):
    nickname = message_start.from_user.first_name
    bot.reply_to(message_start, f"Здравствуйте {nickname}! ")


@bot.message_handler(commands=['help'])
def send_welcome(message_help):
    bot.reply_to(message_help, "Чем я могу Вам помочь?")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.infinity_polling()
