# crm2/keyboards/__init__.py
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
