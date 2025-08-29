# crm2/keyboards/project.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def project_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Как проводятся занятия")],
        [KeyboardButton(text="↩️ Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
