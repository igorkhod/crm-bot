# crm2/keyboards/info_menu.py
# Назначение: Клавиатура информационного меню с выбором потоков и мероприятий
# Функции:
# - info_menu_kb - Адаптивное меню информации о потоках с опциональными мероприятиями
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def info_menu_kb(*, has_events: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="1 поток · набор 09.2023")],
        [KeyboardButton(text="2 поток · набор 04.20225")],
        [KeyboardButton(text="Новый набор · 2026")],
    ]
    if has_events:
        rows.append([KeyboardButton(text="Мероприятия")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
