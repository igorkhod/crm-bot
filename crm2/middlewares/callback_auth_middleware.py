# crm2/middlewares/callback_auth_middleware.py
# Назначение: Middleware для проверки авторизации callback-запросов
# Классы:
# - CallbackAuthMiddleware - Middleware проверки авторизации колбэков
# Методы:
# - __call__ - Основной метод обработки callback-запросов с детальной логикой проверки
# новое описание:
# crm2/middlewares/callback_auth_middleware.py
# Назначение: Middleware для проверки авторизации callback-запросов
# Классы:
# - CallbackAuthMiddleware - Middleware проверки авторизации колбэков
# Методы:
# - __call__ - Основной метод обработки callback-запросов с детальной логикой проверки

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from crm2.services.users import get_user_by_telegram
from crm2.keyboards import guest_start_kb

logger = logging.getLogger(__name__)


class CallbackAuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        logger.info(f"CallbackAuthMiddleware: processing callback data = {event.data}")

        # Пропускаем callback data, которые начинаются с "admin:" - они уже проверены
        if event.data and event.data.startswith('admin:'):
            logger.info(f"CallbackAuthMiddleware: processing admin callback {event.data}")
            user = await get_user_by_telegram(event.from_user.id)
            if user and user.get('nickname') and user.get('password'):
                data['user'] = user
                return await handler(event, data)
            else:
                logger.warning(f"CallbackAuthMiddleware: user not authorized for admin callback")
                await event.message.answer(
                    "⛔️ Доступ ограничен. Пожалуйста, войдите или зарегистрируйтесь.",
                    reply_markup=guest_start_kb()
                )
                await event.answer()
                return

        # Для остальных callback проверяем авторизацию
        user = await get_user_by_telegram(event.from_user.id)
        logger.info(f"CallbackAuthMiddleware: user found = {bool(user)}")

        if not user:
            logger.warning(f"Unauthorized callback from {event.from_user.id}: user not found")
            await event.message.answer(
                "⛔️ Доступ ограничен. Пожалуйста, войдите или зарегистрируйтесь.",
                reply_markup=guest_start_kb()
            )
            await event.answer()
            return

        nickname = user.get('nickname')
        password = user.get('password')
        if not nickname or not nickname.strip() or not password or not password.strip():
            logger.warning(f"User {event.from_user.id} has incomplete profile")
            await event.message.answer(
                "⛔️ Доступ ограничен. Пожалуйста, войдите или зарегистрируйтесь.",
                reply_markup=guest_start_kb()
            )
            await event.answer()
            return

        data['user'] = user
        logger.info(f"CallbackAuthMiddleware: user authorized, proceeding to handler")
        return await handler(event, data)