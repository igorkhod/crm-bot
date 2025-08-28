# crm2/keyboards/agents.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def agents_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🧘 Волевая медитация")],
        [KeyboardButton(text="⚖️ Психотехнологии гармонии")],
        [KeyboardButton(text="↩️ Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
