# crm2/handlers/registration.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from crm2.handlers import consent as consent_handlers
from crm2.handlers.consent import has_consent  # уже есть в consent.py
from crm2.db.users import get_user_by_tg, upsert_user  # безопасное создание/обновление

router = Router()

# ЕДИНЫЙ ключ колбэка для старта регистрации
REG_START = "reg:start"


class Reg(StatesGroup):
    full_name = State()


@router.callback_query(F.data == REG_START)
async def on_register_click(cb: CallbackQuery, state: FSMContext) -> None:
    """Вход из кнопки «Зарегистрироваться» (гостевое меню)."""
    tg_id = cb.from_user.id

    # 1) Без согласия — сперва показываем экран согласия и выходим
    if not has_consent(tg_id):
        await consent_handlers.send_consent(cb.message)
        await cb.answer()
        return

    # 2) Иначе — старт регистрации
    await start_registration(cb.message, state)
    await cb.answer()


async def start_registration(message: Message, state: FSMContext) -> None:
    """Старт регистрации (первый шаг)."""
    await state.set_state(Reg.full_name)
    await message.answer("Введите ваше ФИО:")


@router.message(Reg.full_name)
async def reg_full_name(message: Message, state: FSMContext) -> None:
    """Принимаем ФИО и сохраняем пользователя."""
    full_name = (message.text or "").strip()
    tg_id = message.from_user.id
    username = message.from_user.username or ""

    # Безопасный upsert (создаст, если нет; обновит, если уже есть)
    upsert_user(
        telegram_id=tg_id,
        username=username,
        full_name=full_name,
        role="user",         # по умолчанию — обычный пользователь
        cohort_id=None,      # пока не определяем поток
    )

    await state.clear()
    await message.answer("✅ Готово! Профиль обновлён. Откройте «Главное меню».")
