# === Файл: crm2/main_menu.py
# Назначение: совместимость. Проксирует функции клавиатур в crm2.keyboards,
#             чтобы в проекте была единая точка правды по текстам кнопок.

from aiogram.types import ReplyKeyboardMarkup
from crm2.keyboards import guest_start_kb as _guest_start_kb, role_kb as _role_kb

def guest_start_kb() -> ReplyKeyboardMarkup:
    return _guest_start_kb()

def role_kb(role: str) -> ReplyKeyboardMarkup:
    return _role_kb(role)
