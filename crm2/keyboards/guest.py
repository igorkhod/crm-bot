# crm2/keyboards/guest.py
# Назначение: Базовая клавиатура для гостевого режима (упрощенная версия)
# Функции:
# - guest_start_kb - Минималистичная клавиатура гостя (регистрация и помощь)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def guest_start_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Зарегистрироваться")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True
    )