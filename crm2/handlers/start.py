# crm2/handlers/start.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from crm2.db.users import get_user_by_tg
from crm2.keyboards.main_menu import role_kb

# Подключаем модули онбординга (welcome → consent → registration)
# и безопасно проверяем наличие нужных функций через hasattr
from crm2.handlers import welcome as welcome_handlers
from crm2.handlers import consent as consent_handlers
from crm2.handlers import registration as registration_handlers

router = Router()


def _guest_menu() -> ReplyKeyboardMarkup:
    """
    Клавиатура для незарегистрированных (гостевой экран).
    """
    kb = [
        [KeyboardButton(text="👤 Войти"), KeyboardButton(text="📝 Зарегистрироваться")],
        [KeyboardButton(text="ℹ️ О проекте")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


async def _send_guest_welcome(message: Message) -> None:
    """
    Приветственный экран для гостей.
    """
    # если есть «поэтическое» приветствие — вызываем его
    if hasattr(welcome_handlers, "show_welcome"):
        await welcome_handlers.show_welcome(message)
    else:
        await message.answer(
            "Добро пожаловать в Psytech! 🧭\n"
            "Вы гость. Выберите действие:",
        )
    # показываем гостевое меню
    await message.answer("Выберите действие:", reply_markup=_guest_menu())


async def _send_main_menu(message: Message, role: str) -> None:
    """
    Главный экран для зарегистрированных (user/admin/...).
    """
    await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    /start:
    - нет пользователя в БД → гостевой экран (поэтическое приветствие + меню)
    - есть пользователь и роль != guest → сразу главное меню
    - есть пользователь и роль == guest → гостевой экран
    """
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)

    if not user:
        await _send_guest_welcome(message)
        return

    role = (user.get("role") or "user").strip().lower()
    if role == "guest":
        await _send_guest_welcome(message)
        return

    await _send_main_menu(message, role)


# ─────────────────────────────────────────────────────────────────────────────
# КНОПКА «📝 Зарегистрироваться»
# Запускаем: 1) поэтическое приветствие → 2) согласие на обработку ПД → 3) регистрацию
# Функции ищем «мягко» через hasattr, чтобы не падать, если имена отличаются.
# ─────────────────────────────────────────────────────────────────────────────
@router.message(F.text == "📝 Зарегистрироваться")
async def start_guest_onboarding(message: Message) -> None:
    # 1) Поэтическое приветствие
    if hasattr(welcome_handlers, "show_welcome"):
        await welcome_handlers.show_welcome(message)
    else:
        await message.answer(
            "Добро пожаловать в Psytech! 🌌 Здесь начинается путь из дисциплины в свободу.\n"
            "Ниже — важные шаги для запуска.",
        )

    # 2) Согласие на обработку персональных данных
    if hasattr(consent_handlers, "ask_consent"):
        await consent_handlers.ask_consent(message)
    elif hasattr(consent_handlers, "show_consent"):
        await consent_handlers.show_consent(message)
    else:
        # минимальная заглушка, если модуль есть, но функции отличаются
        await message.answer(
            "Для продолжения требуется согласие на обработку персональных данных.\n"
            "Нажмите «✅ Да, согласен» для продолжения.",
        )

    # 3) Старт регистрации
    if hasattr(registration_handlers, "start_registration"):
        await registration_handlers.start_registration(message)
    elif hasattr(registration_handlers, "cmd_registration"):
        # если у вас команда оформлена как хендлер команды
        await registration_handlers.cmd_registration(message)
    else:
        # минимальная заглушка
        await message.answer("Запуск регистрации… (обратитесь к администратору, если шаг не появился)")



# На всякий случай: если где-то есть кнопка «↩️ Главное меню» — поддержим её здесь
@router.message(F.text.in_({"↩️ Главное меню", "Главное меню"}))
async def back_to_main(message: Message) -> None:
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)
    role = (user.get("role") if user else "user") or "user"
    await _send_main_menu(message, role)
