import telebot
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я твой бот. Чем могу помочь?")  

    application.run_polling()