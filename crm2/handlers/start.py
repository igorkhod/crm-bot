# crm2/handlers/start.py
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from crm2.db.users import get_user_by_tg
from crm2.keyboards.main_menu import role_kb

# Наши онбординг-модули (используем мягко)
from crm2.handlers import welcome as welcome_handlers
from crm2.handlers import consent as consent_handlers
from crm2.handlers import registration as registration_handlers

router = Router()

CONSENT_URL = "https://www.krasnpsytech.ru/FCKrhyrM72sim"
CONSENT_CB = "consent:agree"   # callback-data для кнопки согласия


# ─────────────────────────── Клавиатуры ───────────────────────────

def guest_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Войти"), KeyboardButton(text="📝 Зарегистрироваться")],
            [KeyboardButton(text="ℹ️ О проекте")],
        ],
        resize_keyboard=True
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Открыть документ", url=CONSENT_URL)],
        [InlineKeyboardButton(text="✅ Да, согласен", callback_data=CONSENT_CB)],
    ])


# ─────────────────────────── Вьюшки ───────────────────────────

async def send_guest_welcome(message: Message) -> None:
    # Поэтическое приветствие, если есть
    if hasattr(welcome_handlers, "show_welcome"):
        await welcome_handlers.show_welcome(message)
    else:
        await message.answer(
            "Добро пожаловать в Psytech! 🌌 Здесь начинается путь из дисциплины в свободу.\n"
            "Ниже — важные шаги для запуска."
        )
    await message.answer("Вы гость. Выберите действие:", reply_markup=guest_menu())


async def send_main_menu(message: Message, role: str) -> None:
    await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))


async def show_consent(message: Message) -> None:
    """
    Обязательное согласие. Если в проекте есть готовый хендлер — используем его,
    иначе показываем свою безопасную реализацию с кнопкой подтверждения.
    """
    if hasattr(consent_handlers, "ask_consent"):
        await consent_handlers.ask_consent(message)
        return
    if hasattr(consent_handlers, "show_consent"):
        await consent_handlers.show_consent(message)
        return

    # Наша минимальная версия
    await message.answer(
        "Для продолжения требуется согласие на обработку персональных данных.\n"
        "Ознакомьтесь с документом и подтвердите согласие.",
        reply_markup=consent_keyboard()
    )


# ─────────────────────────── Хэндлеры ───────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)

    if not user:
        await send_guest_welcome(message)
        return

    role = (user.get("role") or "user").strip().lower()
    if role == "guest":
        await send_guest_welcome(message)
        return

    await send_main_menu(message, role)


@router.message(F.text == "📝 Зарегистрироваться")
async def start_guest_onboarding(message: Message, state: FSMContext) -> None:
    # Приветствие
    if hasattr(welcome_handlers, "show_welcome"):
        await welcome_handlers.show_welcome(message)
    else:
        await message.answer(
            "Добро пожаловать в Psytech! 🌌 Здесь начинается путь из дисциплины в свободу.\n"
            "Ниже — важные шаги для запуска."
        )

    # Обязательное согласие (без него дальше не идём)
    await show_consent(message)

    # Здесь мы НЕ запускаем регистрацию сразу — дождёмся клика «✅ Да, согласен»
    # (см. хэндлер на callback ниже)


@router.callback_query(F.data == CONSENT_CB)
async def consent_agreed(cb: CallbackQuery, state: FSMContext):
    """
    Пользователь нажал «✅ Да, согласен».
    После этого — запускаем регистрацию (с передачей state).
    """
    await cb.answer("Спасибо! Согласие получено.")
    msg: Message = cb.message

    # Если в проекте есть готовая функция с state — используем её
    if hasattr(registration_handlers, "start_registration"):
        await registration_handlers.start_registration(msg, state)
        return

    # В некоторых версиях могла быть другая сигнатура
    if hasattr(registration_handlers, "cmd_registration"):
        await registration_handlers.cmd_registration(msg)
        return

    # Запасной вариант (текст-заглушка)
    await msg.answer("Запуск регистрации… (обратитесь к администратору, если шаг не появился)")


@router.message(F.text.in_({"↩️ Главное меню", "Главное меню"}))
async def back_to_main(message: Message) -> None:
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)
    role = (user.get("role") if user else "user") or "user"
    await send_main_menu(message, role)
