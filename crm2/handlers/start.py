# crm2/handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from crm2.keyboards.main_menu import guest_start_kb, role_kb
from crm2.db.users import get_user_by_tg

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    /start:
      - если пользователь найден в БД -> сразу главное меню по его роли;
      - если не найден -> приветствие и гостевое меню.
    """
    tg_id = message.from_user.id

    # get_user_by_tg — синхронная функция, без await
    user = get_user_by_tg(tg_id)

    if user:
        role = user.get("role", "user")
        await message.answer(
            f"Главное меню (ваша роль: {role})",
            reply_markup=role_kb(role),
        )
    else:
        await message.answer(
            "Добро пожаловать в Psytech! 🌌\n"
            "Вы гость. Выберите действие:",
            reply_markup=guest_start_kb(),
        )
