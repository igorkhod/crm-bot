# === Автогенерированный заголовок: crm2/handlers/registration.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: RegistrationFSM
# Функции: start_registration_cb, reg_full_name, reg_phone, reg_email
# === Конец автозаголовка
# crm2/handlers/registration.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from crm2.db.users import get_user_by_tg, upsert_user  # upsert для безопасного создания/обновления

router = Router(name="registration")

# Единый callback-ключ для старта регистрации (его дергает start.py)
REG_START = "registration:start"


class RegistrationFSM(StatesGroup):
    full_name = State()
    phone = State()
    email = State()
    # при необходимости можно добавить password/state и т.п.


@router.callback_query(F.data == REG_START)
async def start_registration_cb(cb, state: FSMContext):
    """Старт из инлайн-кнопки (гостевое меню)."""
    await state.clear()
    await state.set_state(RegistrationFSM.full_name)
    await cb.message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
    await cb.answer()


@router.message(RegistrationFSM.full_name)
async def reg_full_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()
    if not full_name:
        await message.answer("Пожалуйста, укажите ФИО текстом.")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationFSM.phone)
    await message.answer("Введите ваш номер телефона:")


@router.message(RegistrationFSM.phone)
async def reg_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    if not phone:
        await message.answer("Пожалуйста, укажите номер телефона.")
        return

    await state.update_data(phone=phone)
    await state.set_state(RegistrationFSM.email)
    await message.answer("Введите ваш email:")


@router.message(RegistrationFSM.email)
async def reg_email(message: Message, state: FSMContext):
    email = (message.text or "").strip()
    if not email or "@" not in email:
        await message.answer("Пожалуйста, укажите корректный email.")
        return

    data = await state.get_data()
    tg_id = message.from_user.id

    # создаём/обновляем запись пользователя
    upsert_user(
        telegram_id=tg_id,
        username=message.from_user.username,
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        email=email,
        role="user",   # после регистрации — обычный пользователь
        cohort_id=None # можно назначить позже
    )

    await state.clear()
    await message.answer("✅ Регистрация завершена. Добро пожаловать в систему!")
