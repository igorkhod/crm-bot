# /*** /dev/null
## === Файл: crm2/keyboards/info_menu.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def info_menu_kb(*, has_events: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="1 поток · набор 09.2023")],
        [KeyboardButton(text="2 поток · набор 09.2023")],
        [KeyboardButton(text="Новый набор · 2025")],
    ]
    if has_events:
        rows.append([KeyboardButton(text="Мероприятия")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
