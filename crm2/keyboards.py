from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def guest_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="🆕 Зарегистрироваться")],
            [KeyboardButton(text="👀 Просто посмотреть")],
        ],
        resize_keyboard=True
    )

def role_kb(role: str) -> ReplyKeyboardMarkup:
    if role == "curious":
        return guest_kb()
    if role in ("user","long_user"):
        rows = [
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="📚 Материалы")],
            [KeyboardButton(text="ℹ️ Профиль")],
            [KeyboardButton(text="↩️ Выйти в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    if role == "advanced_user":
        rows = [
            [KeyboardButton(text="🧠 Новости психонетики"), KeyboardButton(text="🧪 Новые технологии")],
            [KeyboardButton(text="📚 База знаний")],
            [KeyboardButton(text="↩️ Выйти в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    if role == "admin":
        rows = [
            [KeyboardButton(text="🛠 Панель администратора")],
            [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="✉️ Рассылка")],
            [KeyboardButton(text="↩️ Выйти в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
    return guest_kb()


# === Стартовое меню для гостя (вход / регистрация / обзор) ===================
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def guest_start_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="🆕 Зарегистрироваться")],
            [KeyboardButton(text="👀 Просто посмотреть")],
        ],
        resize_keyboard=True
    )
