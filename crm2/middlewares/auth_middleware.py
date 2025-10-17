# crm2/middlewares/callback_auth_middleware.py
# Назначение: Middleware для проверки авторизации callback-запросов
# Классы:
# - CallbackAuthMiddleware - Middleware проверки авторизации колбэков
# Методы:
# - __call__ - Основной метод обработки callback-запросов с детальной логикой проверки
# crm2/middlewares/auth_middleware.py (исправленная версия)
# новое описание
# crm2/middlewares/auth_middleware.py
# Назначение: Middleware для проверки авторизации входящих сообщений и callback-запросов
# Классы:
# - AuthMiddleware - Middleware проверки авторизации
# Методы:
# - __call__ - Основной метод обработки событий с проверкой авторизации и исключениями для гостевых команд

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from crm2.services.users import get_user_by_telegram


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        # Исключения для гостевых команд и действий
        guest_commands = ['/start', '/login', '/help', '/about', '/register', '/menu', '/cancel']

        # Для CallbackQuery проверяем данные
        if isinstance(event, CallbackQuery):
            # Разрешаем колбэки связанные с аутентификацией
            if event.data and any(auth_key in event.data for auth_key in ['auth', 'login', 'register', 'guest']):
                return await handler(event, data)

        # Для Message проверяем текст команды
        if isinstance(event, Message) and event.text:
            text = event.text.strip()
            if any(text.startswith(cmd) for cmd in guest_commands) or text in ["🔐 Войти", "🆕 Зарегистрироваться",
                                                                               "📖 О проекте", "🔙 Выйти в меню"]:
                return await handler(event, data)

        # Получаем пользователя (БЕЗ AWAIT - функция синхронная!)
        user = await get_user_by_telegram(event.from_user.id)

        if not user or not user.get('nickname') or not user.get('password'):
            # Пользователь не авторизован
            if isinstance(event, Message):
                from crm2.keyboards import guest_start_kb
                await event.answer(
                    "🔐 Для доступа к этому разделу необходимо авторизоваться.\n\n"
                    "Используйте кнопку '🔐 Войти' или команду /start",
                    reply_markup=guest_start_kb()
                )
                return
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Необходимо авторизоваться", show_alert=True)
                return

        # Добавляем пользователя в data для обработчиков
        data['user'] = user
        return await handler(event, data)