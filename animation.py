import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Загрузка токена
load_dotenv("token.env")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# 1. Анимация переливания кнопки DeepSeek
async def animate_deepseek_button(chat_id: int, message_id: int):
    emojis = ["🔷", "🔵", "💠", "🌀", "🌐", "💎"]
    for emoji in emojis * 2:  # 2 полных цикла
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            types.InlineKeyboardButton(text=f"{emoji} DeepSeek", callback_data="deepseek"),
            types.InlineKeyboardButton(text="🤖 OpenAI", callback_data="openai")
        )
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard.as_markup()
            )
            await asyncio.sleep(0.3)  # Скорость анимации
        except:
            break


# 2. Анимация точек в сообщении (гарантированно работает)
async def show_waiting_dots(chat_id: int):
    # dots = ["", ".", "..", "..."]
    # dots = ["●", "●", "●●", "●●●"]
    dots = ["•", "●", "●●", "●●●"]
    msg = await bot.send_message(chat_id, "Подождите, ИИ обрабатывает запрос")

    for _ in range(8):  # 8 циклов (~4 секунды)
        for dot in dots:
            try:
                await msg.edit_text(f"Подождите, ИИ обрабатывает запрос  {dot}")
                await asyncio.sleep(0.25)  # Частота обновления
            except:
                return
    return msg


# 3. Основная клавиатура
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🔷 DeepSeek", callback_data="deepseek"),
        types.InlineKeyboardButton(text="🤖 OpenAI", callback_data="openai")
    )
    return builder.as_markup()


# 4. Обработчики
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Выберите ИИ для запроса:",
        reply_markup=get_main_keyboard()
    )


@dp.callback_query(F.data.in_(["deepseek", "openai"]))
async def handle_ai_selection(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id

    # Запускаем обе анимации параллельно
    button_animation = asyncio.create_task(animate_deepseek_button(chat_id, message_id))
    dots_message = await show_waiting_dots(chat_id)

    # Имитируем обработку (4 секунды)
    await asyncio.sleep(4)

    # Завершаем анимации
    button_animation.cancel()
    await dots_message.delete()

    # Показываем результат
    ai_name = "DeepSeek" if callback.data == "deepseek" else "OpenAI"
    await callback.message.answer(
        f"✅ {ai_name} ответил:\n"
        "Это имитация реального процесса обработки",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


# Запуск
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    print("Бот запущен. Отправьте /start")
    asyncio.run(main())