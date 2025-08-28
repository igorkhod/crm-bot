# crm2/keyboards/__init__.py
# Пакет клавиатур. Реализация в ._impl и вспомогательные сборщики в .schedule.
# Здесь экспортируем всё, что может понадобиться внешним модулям, чтобы
# импорты были стабильными и без циклов.

from ._impl import guest_start_kb, role_kb, guest_kb
from .schedule import format_range, build_schedule_keyboard
from .main_menu import guest_start_kb, role_kb
from .info_menu import info_menu_kb
from .admin_users import users_groups_kb, users_pager_kb
__all__ = [
    'guest_start_kb', 'role_kb', 'guest_kb',
    'format_range', 'build_schedule_keyboard',
    'users_groups_kb', 'users_pager_kb',
]
