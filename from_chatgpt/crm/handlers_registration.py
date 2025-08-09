# 📁 from_chatgpt/crm/handlers_registration.py
# handlers_registration.py — модуль, отвечающий за пошаговую регистрацию новых пользователей с возможностью пропустить шаги.

from aiogram import Router, F # 📦 Импорт из модуля
from aiogram.types import Message, CallbackQuery # 📦 Импорт из модуля
from aiogram.filters import Command # 📦 Импорт из модуля
from aiogram.fsm.context import FSMContext # 📦 Импорт из модуля
from from_chatgpt.crm.keyboards import main_crm_keyboard, skip_button_keyboard # 📦 Импорт из модуля
from from_chatgpt.crm.services import add_user, get_user_by_telegram # 📦 Импорт из модуля

registration_router = Router()

# Временное хранилище (временно вместо FSM)
user_registration_data = {}


# Команда /start — приветствие и проверка
@registration_router.message(Command("start"))
async def registration_start(message: Message):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram(telegram_id)

    if user: # ✅ Условная конструкция
        role = user[6]
        await message.answer( # ⏳ Ожидание асинхронной операции
            f"✅ Вы уже зарегистрированы.\nВаша роль: {'Администратор' if role == 'admin' else 'Курсант'}",
            reply_markup=main_crm_keyboard(role=role)
        )
        return # ↩️ Возврат значения

    user_registration_data[telegram_id] = {}
    await message.answer("👋 Добро пожаловать в CRM!\nПожалуйста, введите ваш Telegram никнейм (nickname):") # ⏳ Ожидание асинхронной операции


# Приём данных поочерёдно
@registration_router.message(F.text)
async def registration_steps(message: Message):
    telegram_id = message.from_user.id
    text = message.text.strip()

    if telegram_id not in user_registration_data: # ✅ Условная конструкция
        await registration_start(message) # ⏳ Ожидание асинхронной операции
        return # ↩️ Возврат значения

    data = user_registration_data[telegram_id]

    if "nickname" not in data: # ✅ Условная конструкция
        data["nickname"] = text
        await message.answer("Введите вашу Фамилию:", reply_markup=skip_button_keyboard()) # ⏳ Ожидание асинхронной операции
    elif "last_name" not in data: # 🔄 Альтернативное условие
        data["last_name"] = text
        await message.answer("Введите ваше Имя:", reply_markup=skip_button_keyboard()) # ⏳ Ожидание асинхронной операции
    elif "first_name" not in data: # 🔄 Альтернативное условие
        data["first_name"] = text
        await message.answer("Введите ваше Отчество:", reply_markup=skip_button_keyboard()) # ⏳ Ожидание асинхронной операции
    elif "middle_name" not in data: # 🔄 Альтернативное условие
        data["middle_name"] = text
        full_name = " ".join(filter(None, [
            data.get("last_name"),
            data.get("first_name"),
            data.get("middle_name"),
        ]))
        await add_user(telegram_id, full_name, data["nickname"]) # ⏳ Ожидание асинхронной операции
        await message.answer( # ⏳ Ожидание асинхронной операции
            f"✅ {full_name}, вы успешно зарегистрированы как Курсант.",
            reply_markup=main_crm_keyboard(role="participant")
        )
        del user_registration_data[telegram_id]


# Пропуск шага
@registration_router.callback_query(F.data == "skip")
async def skip_step(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    user = await get_user_by_telegram(telegram_id)

    # Если уже зарегистрирован
    if user: # ✅ Условная конструкция
        role = user[6]
        await callback.message.answer( # ⏳ Ожидание асинхронной операции
            f"✅ Вы уже зарегистрированы.\nВаша роль: {'Администратор' if role == 'admin' else 'Курсант'}",
            reply_markup=main_crm_keyboard(role=role)
        )
        await state.clear() # ⏳ Ожидание асинхронной операции
        await callback.answer() # ⏳ Ожидание асинхронной операции
        return # ↩️ Возврат значения

    data = user_registration_data.setdefault(telegram_id, {})

    if "nickname" not in data: # ✅ Условная конструкция
        await callback.message.answer("Введите ваш Telegram никнейм (nickname):") # ⏳ Ожидание асинхронной операции
    elif "last_name" not in data: # 🔄 Альтернативное условие
        data["last_name"] = ""
        await callback.message.answer("Введите ваше Имя:", reply_markup=skip_button_keyboard()) # ⏳ Ожидание асинхронной операции
    elif "first_name" not in data: # 🔄 Альтернативное условие
        data["first_name"] = ""
        await callback.message.answer("Введите ваше Отчество:", reply_markup=skip_button_keyboard()) # ⏳ Ожидание асинхронной операции
    elif "middle_name" not in data: # 🔄 Альтернативное условие
        data["middle_name"] = ""
        full_name = " ".join(filter(None, [
            data.get("last_name"),
            data.get("first_name"),
            data.get("middle_name"),
        ]))
        await add_user(telegram_id, full_name, data["nickname"]) # ⏳ Ожидание асинхронной операции
        await callback.message.answer( # ⏳ Ожидание асинхронной операции
            f"✅ {full_name}, вы успешно зарегистрированы как Курсант.",
            reply_markup=main_crm_keyboard(role="participant")
        )
        del user_registration_data[telegram_id]

    await callback.answer() # ⏳ Ожидание асинхронной операции