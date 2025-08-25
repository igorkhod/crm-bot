# crm2/keyboards/__init__.py
# Пакет клавиатур. Реализация в ._impl и вспомогательные сборщики в .schedule.
# Здесь экспортируем всё, что может понадобиться внешним модулям, чтобы
# импорты были стабильными и без циклов.

from ._impl import guest_start_kb, role_kb, guest_kb
from .schedule import format_range, build_schedule_keyboard

__all__ = ['guest_start_kb', 'role_kb', 'guest_kb', 'format_range', 'build_schedule_keyboard']
