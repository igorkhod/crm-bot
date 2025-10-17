from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.types import Message

from crm2.keyboards import role_kb
from crm2.services.users import get_user_by_telegram

# crm2/handlers/main_menu.py
# Назначение: Центральная навигация системы - обработка главного меню для всех ролей пользователей
# Функции: —
# Обработчики:
# - to_main_menu - Переход в главное меню после авторизации с определением роли
# - back_to_main - Универсальный возврат в главное меню (гость/пользователь/админ)
# - handle_admin_button - Проверка прав и перенаправление в админ-панель
# - show_schedule - Обработчик раздела расписания (только авторизованные)
# - show_materials - Обработчик раздела материалов (только авторизованные)
# - show_profile - Обработчик личного кабинета (только авторизованные)
# новая шапка2510151703:
# crm2/handlers/main_menu.py
# Назначение: Центральная навигация системы - обработка главного меню для всех ролей пользователей
# Функции: —
# Обработчики:
# - to_main_menu - Переход в главное меню после авторизации с определением роли
# - back_to_main - Универсальный возврат в главное меню (гость/пользователь/админ)
# - handle_admin_button - Проверка прав и перенаправление в админ-панель
# - show_schedule - Обработчик раздела расписания (только авторизованные)
# - show_materials - Обработчик раздела материалов (только авторизованные)
# - show_profile - Обработчик личного кабинета (только авторизованные)
logger = logging.getLogger(__name__)
router = Router()


# Добавьте в main_menu.py или создайте новый файл
# @router.message(F.text == "🏠 Главное меню")
# async def to_main_menu(message: Message):
# @router.message(F.text == "🏠 Главное меню")
# async def to_main_menu(message: Message):
#     """Переход в главное меню после авторизации"""
#     # Проверяем сначала сессию, потом БД
#     from crm2.handlers.auth import user_sessions
#
#     user_id = message.from_user.id
#     session = user_sessions.get(user_id, {})
#
#     if session.get('authenticated'):
#         # Пользователь авторизован через сессию
#         role = session.get('user_data', {}).get('role', 'user')
#         await message.answer("Главное меню:", reply_markup=role_kb(role))
#         return
#
#     # Если нет сессии, проверяем БД
#     u = await get_user_by_telegram(message.from_user.id)
#     if u and u.get('nickname') and u.get('password'):
#         role = u.get("role", "user")
#         await message.answer("Главное меню:", reply_markup=role_kb(role))
#         return
#
#     # Неавторизован
#     from crm2.keyboards import guest_start_kb
#     await message.answer("Главное меню:", reply_markup=guest_start_kb())


@router.message(F.text == "🏠 Главное меню")
async def to_main_menu(message: Message):
    """Упрощенная версия для тестирования"""
    from crm2.handlers.auth import user_sessions

    user_id = message.from_user.id
    session = user_sessions.get(user_id, {})

    if session.get('authenticated'):
        role = session.get('user_data', {}).get('role', 'user')
        await message.answer("Главное меню:", reply_markup=role_kb(role))
    else:
        from crm2.keyboards import guest_start_kb
        await message.answer("Главное меню:", reply_markup=guest_start_kb())

@router.message(F.text == "🔙 Выйти в меню")
async def back_to_main(message: Message):
    """Возврат в главное меню с учетом роли"""
    u = await get_user_by_telegram(message.from_user.id)

    if not u or not u.get('nickname') or not u.get('password'):
        # Неавторизованный пользователь - в гостевое меню
        from crm2.keyboards import guest_start_kb
        await message.answer("Главное меню:", reply_markup=guest_start_kb())
        return

    role = u.get("role", "user")
    await message.answer("Главное меню:", reply_markup=role_kb(role))


@router.message(F.text == "⚙️ Админ")
async def handle_admin_button(message: Message):
    """Обработчик кнопки админ-панели в главном меню"""
    u = await get_user_by_telegram(message.from_user.id)

    if not u or u.get("role") != "admin":
        await message.answer("⛔️ Доступ только для администраторов.")
        return

    # Перенаправляем в админ-панель
    from crm2.handlers.admin.panel import open_admin_menu
    await open_admin_menu(message)


# Обработчики других кнопок главного меню (только для авторизованных)
@router.message(F.text == "📅 Расписание")
async def show_schedule(message: Message):
    u = await get_user_by_telegram(message.from_user.id)
    if not u or not u.get('nickname'):
        return

    # Используем существующий обработчик из info.py
    from crm2.handlers.info import show_schedule_menu
    await show_schedule_menu(message)


@router.message(F.text == "📦 Материалы")
async def show_materials(message: Message):
    u = await get_user_by_telegram(message.from_user.id)
    if not u or not u.get('nickname'):
        return
    await message.answer("📦 Раздел материалов...")


# @router.message(F.text == "👤 Личный кабинет")
# async def show_profile(message: Message):
@router.message(F.text == "👤 Личный кабинет")
async def show_profile(message: Message):
    u = await get_user_by_telegram(message.from_user.id)
    if not u or not u.get('nickname'):
        await message.answer("❌ Для доступа к личному кабинету нужно завершить регистрацию.")
        return

    # Импортируем и вызываем функцию show_profile из profile.py
    from crm2.handlers.profile import show_profile as show_profile_handler
    await show_profile_handler(message)