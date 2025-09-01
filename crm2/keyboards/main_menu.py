# crm2/keyboards/main_menu.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    """
    Главное пользовательское меню.
    Совместимо с существующей логикой start.py (именно это имя функции импортируется).
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="📦 Материалы")],
            [KeyboardButton(text="👤 Личный кабинет")],
            [KeyboardButton(text="🧠 ИИ-агенты"), KeyboardButton(text="⚙️ Админ")],
            [KeyboardButton(text="🔙 Выйти в меню")],
        ],
        resize_keyboard=True
    )
