# crm2/keyboards/profile.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def profile_menu_kb():
    rows = [
        [KeyboardButton(text="🔔 Уведомления: вкл/выкл")],
        [KeyboardButton(text="📄 Мои материалы")],
        [KeyboardButton(text="↩️ Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
