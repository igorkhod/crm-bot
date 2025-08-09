# handlers.py — модуль с Telegram-хендлерами CRM-системы.
# Обрабатывает команду /crm и регистрацию участников на потоки через CallbackQuery.

from aiogram import F, Router, Dispatcher # 📦 Импорт из модуля
from aiogram.types import Message, CallbackQuery # 📦 Импорт из модуля
from aiogram.filters import Command # 📦 Импорт из модуля

from .keyboards import main_crm_keyboard # 📦 Импорт из модуля
from .services import get_user_by_telegram, register_participant # 📦 Импорт из модуля

crm_router = Router()


# Хендлер для команды /crm
async def start_crm(message: Message):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram(telegram_id)

    if not user: # ✅ Условная конструкция
        await message.answer("Вы не зарегистрированы в системе. Пожалуйста, используйте /start для регистрации.") # ⏳ Ожидание асинхронной операции
        return # ↩️ Возврат значения

    role = user[5]  # Индекс поля 'role' в выборке SELECT * FROM users
    role_name = "Администратор" if role == "admin" else "Курсант"

    await message.answer( # ⏳ Ожидание асинхронной операции
        f"Добро пожаловать в CRM!\nВаша роль: {role_name}",
        reply_markup=main_crm_keyboard(role=role)
    )


# Хендлер для регистрации на поток
async def register_to_stream(callback: CallbackQuery):
    try: # 🛑 Блок обработки ошибок (try)
        stream_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError): # ⚠️ Обработка исключения
        await callback.answer("Ошибка: некорректный идентификатор потока") # ⏳ Ожидание асинхронной операции
        return # ↩️ Возврат значения

    telegram_id = callback.from_user.id
    success = await register_participant(telegram_id, stream_id)

    if success: # ✅ Условная конструкция
        await callback.answer("Вы успешно записаны на поток!") # ⏳ Ожидание асинхронной операции
    else: # 🔚 Иначе (альтернатива)
        await callback.answer("Вы уже зарегистрированы на этот поток или произошла ошибка") # ⏳ Ожидание асинхронной операции


# Регистрация всех хендлеров CRM в диспетчере
def register_crm_handlers(dp: Dispatcher): # 🔧 Определение функции/метода
    dp.message.register(start_crm, Command("crm"))
    dp.callback_query.register(register_to_stream, F.data.startswith("register:"))