#
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def guest_start_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="📝 Регистрация"), KeyboardButton(text="📖 О проекте")],
        ],
        resize_keyboard=True
    )

def role_kb(role: str) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="ℹ️ Информация"), KeyboardButton(text="🏠 Меню"), KeyboardButton(text="📖 О проекте")],
    ]
    if (role or "").lower() == "admin":
        rows.insert(0, [KeyboardButton(text="🛠 Панель администратора")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
