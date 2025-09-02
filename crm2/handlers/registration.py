# crm2/handlers/registration.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from crm2.db.users import (
    get_user_by_tg,
    get_user_by_nickname,
    upsert_user,
)

router = Router(name="registration")

# Для совместимости (раньше стартовали из inline-колбэка)
REG_START = "registration:start"


class RegistrationFSM(StatesGroup):
    full_name = State()
    phone = State()
    email = State()
    nickname = State()
    password = State()


# ───────────────────────────────────────────────────────────────────────────────
# СТАРТ РЕГИСТРАЦИИ (reply-кнопка «Зарегистрироваться»)
# ───────────────────────────────────────────────────────────────────────────────
@router.message(F.text.contains("Зарегистрироваться"))
async def start_registration_msg(message: Message, state: FSMContext):
    """Старт регистрации из reply-кнопки."""
    await state.clear()
    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


# (Опционально, если где-то остались inline-кнопки)
@router.callback_query(F.data == REG_START)
async def start_registration_cb(cb, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationFSM.full_name)
    await cb.message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
    await cb.answer()


# ───────────────────────────────────────────────────────────────────────────────
# ШАГИ FSM
# ───────────────────────────────────────────────────────────────────────────────
@router.message(RegistrationFSM.full_name)
async def reg_full_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer("Имя слишком короткое. Повторите, пожалуйста:")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationFSM.phone)
    await message.answer("Введите ваш номер телефона (+7…):")


@router.message(RegistrationFSM.phone)
async def reg_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    # мягкая валидация
    if not any(ch.isdigit() for ch in phone):
        await message.answer("Похоже, это не номер. Введите телефон ещё раз:")
        return
    await state.update_data(phone=phone)
    await state.set_state(RegistrationFSM.email)
    await message.answer("Введите ваш email:")


@router.message(RegistrationFSM.email)
async def reg_email(message: Message, state: FSMContext):
    email = (message.text or "").strip()
    if "@" not in email or "." not in email:
        await message.answer("Похоже, это не email. Введите корректный email:")
        return
    await state.update_data(email=email)
    await state.set_state(RegistrationFSM.nickname)
    await message.answer("Введите **никнейм** (латиница/цифры, без пробелов):")


@router.message(RegistrationFSM.nickname)
async def reg_nickname(message: Message, state: FSMContext):
    nickname = (message.text or "").strip()
    if not nickname or " " in nickname:
        await message.answer("Никнейм не должен содержать пробелов. Введите ещё раз:")
        return
    # Проверка на уникальность
    exist = get_user_by_nickname(nickname)
    tg_id = message.from_user.id
    # Разрешаем, если ник уже за текущим пользователем (повторная регистрация)
    if exist and exist.get("telegram_id") != tg_id:
        await message.answer("Такой ник уже занят. Укажите другой никнейм:")
        return

    await state.update_data(nickname=nickname)
    await state.set_state(RegistrationFSM.password)
    await message.answer("Введите **пароль** (не менее 4 символов):")


@router.message(RegistrationFSM.password)
async def reg_password(message: Message, state: FSMContext):
    password = (message.text or "").strip()
    if len(password) < 4:
        await message.answer("Короткий пароль. Введите пароль длиной от 4 символов:")
        return

    tg_id = message.from_user.id
    data = await state.get_data()

    # Создаём/обновляем пользователя — сохраняем nickname и password в существующие поля.
    upsert_user(
        telegram_id=tg_id,
        username=message.from_user.username,
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        nickname=data.get("nickname", ""),
        password=password,              # Валидация/хеширование решаются в auth-слое; здесь — запись как есть
        role="user",
        cohort_id=None,
    )

    await state.clear()
    await message.answer("✅ Регистрация завершена. Добро пожаловать в систему!")
