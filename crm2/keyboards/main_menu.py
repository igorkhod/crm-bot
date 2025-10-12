# crm2/keyboards/main_menu.py
# Назначение: Универсальная клавиатура главного меню с поддержкой ролевой модели
# Функции:
# - main_menu_kb - Главное меню системы с базовыми разделами и опциональной админ-кнопкой
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb(role: str = "user") -> ReplyKeyboardMarkup:
    base_buttons = [
        [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="📦 Материалы")],
        [KeyboardButton(text="ℹ️ Информация о проекте")],
        [KeyboardButton(text="👤 Личный кабинет")],
        [KeyboardButton(text="🧠 ИИ-агенты")],
    ]

    # Добавляем кнопку админа если нужно
    if role == "admin":
        base_buttons.append([KeyboardButton(text="⚙️ Админ")])

    base_buttons.append([KeyboardButton(text="🔙 Выйти в меню")])

    return ReplyKeyboardMarkup(
        keyboard=base_buttons,
        resize_keyboard=True
    )