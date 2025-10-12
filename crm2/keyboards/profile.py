# crm2/keyboards/profile.py
# Назначение: Клавиатура личного кабинета с настройками пользователя
# Функции:
# - profile_menu_kb - Меню личного кабинета: поток, уведомления, материалы
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