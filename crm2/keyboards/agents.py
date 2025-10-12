# crm2/keyboards/agents.py
# Назначение: Reply-клавиатура меню ИИ-агентов с инструкциями и ссылками
# Функции:
# - agents_menu_kb - Меню агентов: инструкция, медитация, гармония, возврат
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def agents_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Инструкция по подключению ChatGPT-АГЕНТОВ")],
        [KeyboardButton(text="🧘 Волевая медитация (необходима VPN)")],
        [KeyboardButton(text="⚖️ Психотехнологии гармонии (необходима VPN)")],
        [KeyboardButton(text="↩️ Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
