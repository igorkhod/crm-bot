#
# === Файл: crm2/keyboards.py
# Аннотация: модуль CRM, Telegram-бот на aiogram 3.x. Внутри функции: guest_kb, role_kb, guest_start_kb.
# Добавлено автоматически 2025-08-21 05:43:17

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def guest_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="🆕 Зарегистрироваться"), KeyboardButton(text="👀 Просто посмотреть")],
        ],
        resize_keyboard=True
    )


def role_kb(role: str) -> ReplyKeyboardMarkup:
    # гости — как раньше
    if role == "curious":
        return guest_kb()

    # обычный пользователь
    if role in ("user", "long_user"):
        rows = [
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="📚 Материалы"), KeyboardButton(text="ℹ️ Профиль")],
            [KeyboardButton(text="🤖 ИИ-агенты"), KeyboardButton(text="↩️ Выйти в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    # продвинутый
    if role == "advanced_user":
        rows = [
            [KeyboardButton(text="🧠 Новости психонетики"), KeyboardButton(text="🧪 Новые технологии")],
            [KeyboardButton(text="📚 База знаний")],
            [KeyboardButton(text="↩️ Выйти в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    # админ — добавляем кнопку входа в админ-панель
    if role == "admin":
        rows = [
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="📚 Материалы"), KeyboardButton(text="ℹ️ Профиль")],
            [KeyboardButton(text="🤖 ИИ-агенты"), KeyboardButton(text="⚙️ Админ"), KeyboardButton(text="↩️ Выйти в меню")],
        ]
        return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

    # на всякий случай
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