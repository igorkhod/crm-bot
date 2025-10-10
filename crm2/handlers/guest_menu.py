# crm2/handlers/guest_menu.py
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from crm2.services.users import get_user_by_telegram
from crm2.keyboards import guest_start_kb, role_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🔐 Войти")
async def guest_login(message: Message, state: FSMContext):
    """Обработчик кнопки входа в гостевом меню"""
    u = get_user_by_telegram(message.from_user.id)

    if u and u.get("nickname") and u.get("password"):
        # Пользователь существует - предлагаем войти
        await message.answer(
            "🔐 Вход в систему\n\n"
            "Пожалуйста, введите ваш пароль для входа:"
        )
        # Здесь можно добавить FSM для обработки ввода пароля
        await state.set_state("waiting_password")
    else:
        await message.answer(
            "❌ Учетная запись не найдена.\n"
            "Возможно, вы еще не зарегистрированы. "
            "Пожалуйста, пройдите регистрацию.",
            reply_markup=guest_start_kb()
        )


@router.message(F.text == "🆕 Зарегистрироваться")
async def guest_register(message: Message):
    """Обработчик кнопки регистрации в гостевом меню"""
    u = get_user_by_telegram(message.from_user.id)

    if u and u.get("nickname") and u.get("password"):
        await message.answer(
            "✅ Вы уже зарегистрированы!\n"
            "Используйте кнопку '🔐 Войти' для входа в систему.",
            reply_markup=guest_start_kb()
        )
    else:
        # Перенаправляем в модуль регистрации
        from crm2.handlers.registration import start_registration
        await start_registration(message)


@router.message(F.text == "📖 О проекте")
async def guest_about(message: Message):
    """Обработчик кнопки 'О проекте' в гостевом меню"""
    await message.answer(
        "🧠 **Psytech CRM**\n\n"
        "Это специализированная система для управления учебными процессами "
        "в рамках психонетических практик.\n\n"
        "Возможности системы:\n"
        "• 📅 Управление расписанием занятий\n"
        "• ✅ Отслеживание посещаемости\n"
        "• 📚 Работа с домашними заданиями\n"
        "• 👥 Управление учебными группами\n\n"
        "Для доступа к полному функционалу требуется регистрация.",
        reply_markup=guest_start_kb()
    )


@router.message(F.text == "🔙 Выйти в меню")
async def back_to_guest_menu(message: Message):
    """Возврат в гостевое меню"""
    await message.answer(
        "Главное меню:",
        reply_markup=guest_start_kb()
    )