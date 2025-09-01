# === Автогенерированный заголовок: crm2/keyboards/admin_attendance.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: choose_cohort_kb
# === Конец автозаголовка
# crm2/keyboards/admin_attendance.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def choose_cohort_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 поток · набор 09.2023"), KeyboardButton(text="2 поток · набор 04.2025")],
            [KeyboardButton(text="✍️ Внести данные"), KeyboardButton(text="💳 Оплата"), KeyboardButton(text="👁 Посмотреть")],
            [KeyboardButton(text="↩️ Главное меню")],
        ],
        resize_keyboard=True
    )
