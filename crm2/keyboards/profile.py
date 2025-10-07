# === Автогенерированный заголовок: crm2/keyboards/profile.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: profile_menu_kb
# === Конец автозаголовка
# crm2/keyboards/profile.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def profile_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧭 Установить поток")
    kb.button(text="🔔 Уведомления: вкл/выкл")
    kb.button(text="📄 Мои материалы")
    kb.button(text="⬅️ В главное меню")
    kb.adjust(2, 2)  # по желанию
    return kb.as_markup(resize_keyboard=True)