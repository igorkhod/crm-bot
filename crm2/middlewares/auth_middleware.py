# crm2/middlewares/callback_auth_middleware.py
# Назначение: Middleware для проверки авторизации callback-запросов
# Классы:
# - CallbackAuthMiddleware - Middleware проверки авторизации колбэков
# Методы:
# - __call__ - Основной метод обработки callback-запросов с детальной логикой проверки
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

from crm2.services.users import get_user_by_telegram
from crm2.keyboards import guest_start_kb


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # Пропускаем команду /start и гостевые кнопки
        allowed_commands = ['/start', '🔐 Войти', '🆕 Зарегистрироваться', '📖 О проекте', '🔙 Выйти в меню']

        if event.text in allowed_commands:
            return await handler(event, data)

        # Проверяем авторизацию для остальных команд
        user = get_user_by_telegram(event.from_user.id)

        if not user or not user.get('nickname') or not user.get('password'):
            await event.answer(
                "⛔️ Доступ ограничен. Пожалуйста, войдите или зарегистрируйтесь.",
                reply_markup=guest_start_kb()
            )
            return

        # Добавляем пользователя в данные
        data['user'] = user
        return await handler(event, data)