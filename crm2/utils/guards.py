# crm2\utils\guards.py"
"""
Модуль guards.py - фильтры контроля доступа для Telegram бота

Назначение: предоставляет фильтры для ограничения доступа к обработчикам
на основе ролей пользователей и других условий.

Классы:
- AdminOnly - фильтр, разрешающий доступ только пользователям с ролью 'admin'

Использование:
from crm2.utils.guards import AdminOnly

router = Router()
router.message.filter(AdminOnly())
router.callback_query.filter(AdminOnly())
"""

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from crm2.db.core import get_db_connection


class AdminOnly(Filter):
    """
    Фильтр для проверки прав администратора
    Разрешает доступ только пользователям с ролью 'admin'
    """

    async def __call__(self, update: Union[Message, CallbackQuery]) -> bool:
        if isinstance(update, Message):
            user_id = update.from_user.id
        elif isinstance(update, CallbackQuery):
            user_id = update.from_user.id
        else:
            return False

        # Используем синхронное подключение к БД
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT role FROM users WHERE telegram_id = ?",
                (user_id,)
            ).fetchone()

        return user and user['role'] == 'admin'
