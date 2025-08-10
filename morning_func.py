import telebot
from telebot import types
import random
import datetime
import time

TOKEN = "8101400368:AAGnAFPEXm_uHyeCblaj-WQUPMLUYvEZ-n4"
bot = telebot.TeleBot(TOKEN)


def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("🌄 Утро", callback_data="show_morning_menu"),
        types.InlineKeyboardButton("📊 Основное", callback_data="main_functions"),
        types.InlineKeyboardButton("⚙ Настройки", callback_data="settings")
    ]
    markup.add(*buttons)
    return markup


def morning_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("☕ Кофе", callback_data="morning_coffee"),
        types.InlineKeyboardButton("📰 Новости", callback_data="morning_news"),
        types.InlineKeyboardButton("🌤️ Погода", callback_data="morning_weather"),
        types.InlineKeyboardButton("📅 Планер", callback_data="morning_plans"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    ]
    markup.add(*buttons)
    return markup


# Обработчик для всех нереализованных кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_all_buttons(call):
    try:
        if call.data == "show_morning_menu":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🌅 Выберите утреннюю функцию:",
                reply_markup=morning_menu()
            )

        elif call.data == "morning_coffee":
            msg = bot.send_animation(
                chat_id=call.message.chat.id,
                animation="https://media.giphy.com/media/3o7TKsrfldgW9MfH44/giphy.gif",
                caption="Ваш виртуальный ☕ готовится..."
            )
            time.sleep(2)
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=msg.message_id,
                caption="☕ Кофе готов! Приятного дня!"
            )

        elif call.data == "morning_plans":
            plans = [
                "1. 7:30 - Зарядка и душ",
                "2. 8:00 - Полезный завтрак",
                "3. 9:00 - Важные задачи дня"
            ]
            bot.send_message(
                call.message.chat.id,
                "📋 *Пример утреннего расписания:*\n" + "\n".join(plans),
                parse_mode="Markdown"
            )

        elif call.data == "back_to_main":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Возвращаемся в главное меню...",
                reply_markup=main_menu()
            )

        else:
            # Для всех остальных кнопок
            bot.answer_callback_query(
                call.id,
                "⏳ Эта кнопка пока в разработке!",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Ошибка: {e}")
        bot.answer_callback_query(
            call.id,
            "⚠️ Произошла ошибка. Попробуйте позже.",
            show_alert=True
        )


@bot.message_handler(commands=['start'])
def start(message):
    hour = datetime.datetime.now().hour
    greeting = random.choice([
        "🌄 Доброе утро, заряжаемся энергией!",
        "☀️ Утро доброе! Как настроение?",
        "🌻 Привет, ранняя пташка!"
    ]) if 5 <= hour < 12 else "🏠 Добро пожаловать!"

    bot.send_message(
        message.chat.id,
        f"{greeting}\nВыберите раздел:",
        reply_markup=main_menu()
    )


if __name__ == '__main__':
    print("Бот запущен! Отправьте /start")
    bot.infinity_polling()