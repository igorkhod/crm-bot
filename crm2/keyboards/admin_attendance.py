# crm2/keyboards/admin_attendance.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def choose_stream_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 поток · набор 09.2023")],
            [KeyboardButton(text="2 поток · набор 04.2025")],
            [KeyboardButton(text="👁 Посмотреть"), KeyboardButton(text="↩️ Главное меню")],
        ],
        resize_keyboard=True
    )
