# === Автогенерированный заголовок: crm2/keyboards/profile.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: profile_menu_kb
# === Конец автозаголовка
# crm2/keyboards/profile.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def profile_menu_kb():
    rows = [
        [KeyboardButton(text="🔔 Уведомления: вкл/выкл")],
        [KeyboardButton(text="📄 Мои материалы")],
        [KeyboardButton(text="↩️ Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
