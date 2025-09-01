# === Автогенерированный заголовок: crm2/keyboards/project.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: project_menu_kb
# === Конец автозаголовка
# crm2/keyboards/project.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def project_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Как проводятся занятия")],
        [KeyboardButton(text="↩️ Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
