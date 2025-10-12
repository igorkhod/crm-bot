from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

# crm2/handlers/start.py
# Назначение: Обработчик команды /start - точка входа в систему для всех пользователей
# Функции:
# - _profile_complete - Проверка завершенности регистрации пользователя
# Обработчики:
# - cmd_start - Основной обработчик команды /start, всегда показывает гостевое меню

from crm2.services.users import get_user_by_telegram
from crm2.keyboards import guest_start_kb, role_kb

logger = logging.getLogger(__name__)
router = Router()


def _profile_complete(u: dict | None) -> bool:
    """Проверяет, завершена ли регистрация пользователя"""
    if not u:
        return False
    nick = (u.get("nickname") or "").strip()
    pwd = (u.get("password") or "").strip()
    return bool(nick and pwd)


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start - ВСЕГДА начинаем с гостевого меню"""
    try:
        # ВСЕГДА показываем гостевое меню при команде /start
        # независимо от авторизации пользователя
        await message.answer(
            "🧠 Добро пожаловать в Psytech CRM!\n\n"
            "Здесь начинается ваш путь из дисциплины в свободу. "
            "Для доступа к полному функционалу необходимо войти или зарегистрироваться.",
            reply_markup=guest_start_kb()
        )

    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer(
            "Добро пожаловать! Выберите действие:",
            reply_markup=guest_start_kb()
        )


    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer(
            "Добро пожаловать! Выберите действие:",
            reply_markup=guest_start_kb()
        )