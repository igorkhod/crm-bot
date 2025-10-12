# crm2/keyboards/__init__.py
# Назначение: Инициализация пакета клавиатур - центральный экспорт всех клавиатур системы
# Экспортирует:
# - guest_start_kb, role_kb, guest_kb - базовые клавиатуры
# - main_menu_kb - главное меню
# - format_range, build_schedule_keyboard - утилиты расписания
# - info_menu_kb - меню информации
# - users_groups_kb, users_pager_kb - клавиатуры пользователей
# - schedule_root_kb, schedule_dates_kb - клавиатуры расписания
# - admin_panel_kb - панель администратора
from ._impl import guest_start_kb, role_kb, guest_kb
from .main_menu import main_menu_kb
from .schedule import format_range, build_schedule_keyboard
from .info_menu import info_menu_kb
from .admin_users import users_groups_kb, users_pager_kb
from .schedule import schedule_root_kb, schedule_dates_kb
from .admin_panel import admin_panel_kb   # ✅ добавили

__all__ = [
    "guest_start_kb", "role_kb", "guest_kb",
    "main_menu_kb",
    "format_range", "build_schedule_keyboard",
    "info_menu_kb",
    "users_groups_kb", "users_pager_kb",
    "schedule_root_kb", "schedule_dates_kb",
    "admin_panel_kb",  # ✅ экспортируем
]


def guest_start_kb():
    """Клавиатура для гостевого меню"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="🆕 Зарегистрироваться")],
            [KeyboardButton(text="📖 О проекте"), KeyboardButton(text="🔙 Выйти в меню")]
        ],
        resize_keyboard=True
    )