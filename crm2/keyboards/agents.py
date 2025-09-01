# === Автогенерированный заголовок: crm2/keyboards/agents.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: agents_menu_kb
# === Конец автозаголовка
# crm2/keyboards/agents.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def agents_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Инструкция по подключению ChatGPT-АГЕНТОВ")],
        [KeyboardButton(text="🧘 Волевая медитация (необходима VPN)")],
        [KeyboardButton(text="⚖️ Психотехнологии гармонии (необходима VPN)")],
        [KeyboardButton(text="↩️ Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
