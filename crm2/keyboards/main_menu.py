# === Автогенерированный заголовок: crm2/keyboards/main_menu.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: main_menu_kb
# === Конец автозаголовка
# crm2/keyboards/main_menu.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="📦 Материалы")],
            [KeyboardButton(text="ℹ️ Информация о проекте")],   # ← добавить
            [KeyboardButton(text="👤 Личный кабинет")],
            [KeyboardButton(text="🧠 ИИ-агенты"), KeyboardButton(text="⚙️ Админ")],
            [KeyboardButton(text="🔙 Выйти в меню")],
        ],
        resize_keyboard=True
    )
