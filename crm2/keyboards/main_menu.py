#
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def guest_start_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="📝 Регистрация")]
        ],
        resize_keyboard=True
    )

def role_kb(role: str) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="ℹ️ Информация"), KeyboardButton(text="🏠 Меню")],
    ]
    if (role or "").lower() == "admin":
        rows.insert(0, [KeyboardButton(text="🛠 Панель администратора")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
