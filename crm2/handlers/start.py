# crm2/handlers/start.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from crm2.db.users import get_user_by_tg
from crm2.keyboards.main_menu import role_kb

# (опционально) если захочешь переиспользовать готовое приветствие — раскомментируй:
# from crm2.handlers import welcome as welcome_handlers

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
    # Если есть готовая функция приветствия — можно вызвать её вместо текста ниже:
    # await welcome_handlers.show_welcome(message)
    await message.answer(
        "Добро пожаловать в Psytech! 🧭\n"
        "Вы гость. Выберите действие:",
        reply_markup=_guest_menu(),
    )


async def _send_main_menu(message: Message, role: str) -> None:
    """
    Главный экран для зарегистрированных (user/admin/...).
    """
    await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    /start:
    - нет пользователя в БД → гостевой экран (приветствие + «Войти/Зарегистрироваться/О проекте»)
    - есть пользователь и роль != guest → сразу главное меню
    """
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)

    if not user:
        # Новый пользователь — показываем приветствие гостя
        await _send_guest_welcome(message)
        return

    role = (user.get("role") or "user").strip().lower()
    if role == "guest":
        # В БД есть запись, но это гость — тоже показываем гостевой экран
        await _send_guest_welcome(message)
        return

    # Зарегистрированный пользователь — сразу в главное меню
    await _send_main_menu(message, role)


# На всякий случай: если где-то есть кнопка «↩️ Главное меню» — поддержим её здесь
@router.message(F.text.in_({"↩️ Главное меню", "Главное меню"}))
async def back_to_main(message: Message) -> None:
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)
    role = (user.get("role") if user else "user") or "user"
    await _send_main_menu(message, role)
