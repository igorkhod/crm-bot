from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup

from crm2.services.users import get_user_by_telegram
from crm2.keyboards import guest_start_kb, role_kb

logger = logging.getLogger(__name__)
router = Router()


class GuestLoginStates(StatesGroup):
    waiting_password = State()


@router.message(Command("start"))
async def guest_start(message: Message):
    """Обработчик команды /start для гостей"""
    u = get_user_by_telegram(message.from_user.id)

    if u and u.get("nickname") and u.get("password"):
        # Пользователь уже зарегистрирован - предлагаем войти
        await message.answer(
            "🔐 Вы уже зарегистрированы!\n"
            "Используйте кнопку '🔐 Войти' для входа в систему.",
            reply_markup=guest_start_kb()
        )
    else:
        # Новый пользователь - показываем гостевое меню
        await message.answer(
            "👋 Добро пожаловать в Psytech CRM!\n\n"
            "Выберите действие:",
            reply_markup=guest_start_kb()
        )


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
        await state.set_state(GuestLoginStates.waiting_password)
    else:
        await message.answer(
            "❌ Учетная запись не найдена.\n"
            "Возможно, вы еще не зарегистрированы. "
            "Пожалуйста, пройдите регистрацию.",
            reply_markup=guest_start_kb()
        )


@router.message(GuestLoginStates.waiting_password)
async def process_login_password(message: Message, state: FSMContext):
    """Обработка введенного пароля"""
    password = message.text.strip()
    u = get_user_by_telegram(message.from_user.id)

    # Здесь должна быть реальная проверка пароля
    # Сейчас просто заглушка
    if u and u.get("password") == password:  # В реальности нужно хеширование
        await message.answer(
            "✅ Вход выполнен успешно!",
            reply_markup=role_kb(u.get("role", "user"))
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Неверный пароль. Попробуйте еще раз или нажмите /start для возврата в меню."
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
        # Используем команду вместо прямого импорта
        from crm2.bot import bot, dp
        await message.answer(
            "📝 Для регистрации используйте команду /register\n"
            "или перейдите по ссылке: /register"
        )


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
@router.message(Command("menu"))
async def back_to_guest_menu(message: Message, state: FSMContext):
    """Возврат в гостевое меню"""
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=guest_start_kb()
    )


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=guest_start_kb()
    )