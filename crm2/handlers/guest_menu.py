# guest_menu.py
# Путь: crm2/handlers/guest_menu.py
# Назначение: Гостевое меню для неаутентифицированных пользователей, вход в систему
# Классы:
#
# GuestLoginStates - Состояния FSM для гостевого входа (waiting_password)
# Функции:
#
# guest_start - Обработчик команды /start для гостей
#
# guest_login - Обработчик кнопки "Войти" (переход в процесс аутентификации)
#
# process_login_password - Обработка введенного пароля с автоматическим хешированием
from __future__ import annotations

import logging
# "\crm2\handlers\guest_menu.py"
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from crm2.keyboards import guest_start_kb, role_kb
from crm2.services.users import get_user_by_telegram, update_user_password  # Импортируем update_user_password
from crm2.utils.password_utils import verify_and_upgrade_password, \
    normalize_string  # Импортируем verify_and_upgrade_password

logger = logging.getLogger(__name__)
router = Router()


class GuestLoginStates(StatesGroup):
    waiting_password = State()


@router.message(Command("start"))
async def guest_start(message: Message):
    u = await get_user_by_telegram(message.from_user.id)

    if u and u.get("nickname") and u.get("password"):
        await message.answer(
            f"✅ Добро пожаловать, {u.get('nickname', 'пользователь')}!\n\n"
            "Выберите действие:",
            reply_markup=role_kb(u.get("role", "user"))
        )
    else:
        await message.answer(
            "👋 Добро пожаловать в Psytech CRM!\n\n"
            "Выберите действие:",
            reply_markup=guest_start_kb()
        )


@router.message(F.text == "🔐 Войти")
async def guest_login(message: Message, state: FSMContext):
    # Всегда запускаем полный процесс аутентификации через команду /login
    from crm2.handlers.auth import cmd_login
    await cmd_login(message, state)


@router.message(GuestLoginStates.waiting_password)
async def process_login_password(message: Message, state: FSMContext):
    """Обработка введенного пароля с автоматическим хешированием"""
    password = normalize_string(message.text.strip())
    u = await get_user_by_telegram(message.from_user.id)

    if not u:
        await message.answer("❌ Ошибка: пользователь не найден")
        await state.clear()
        return

    stored_password = u.get("password", "")

    # ОТЛАДОЧНЫЙ ВЫВОД
    print(f"[DEBUG] User object: {u}")
    print(f"[DEBUG] Nickname: {u.get('nickname')}")
    print(f"[DEBUG] Role: {u.get('role')}")
    print(f"[DEBUG] All keys: {list(u.keys())}")

    # Используем улучшенную проверку с авто-обновлением хеша
    success, new_hash = verify_and_upgrade_password(password, stored_password)

    if success:
        # Если пароль был в plain text - обновляем его в базе
        if new_hash != stored_password:
            await update_user_password(message.from_user.id, new_hash)
            logger.info(f"Password upgraded to bcrypt for user {u.get('nickname')}")

        # Улучшенное приветствие с проверкой данных
        nickname = u.get('nickname', 'пользователь')
        role = u.get('role', 'user')

        print(f"[DEBUG] Final nickname: {nickname}")
        print(f"[DEBUG] Final role: {role}")

        await message.answer(
            f"✅ Вход выполнен успешно, {nickname}!",
            reply_markup=role_kb(role)
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Неверный пароль. Попробуйте еще раз или нажмите /start для возврата в меню."
        )

# ... остальные обработчики ...
