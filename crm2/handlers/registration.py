# crm2/handlers/registration.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.keyboards import guest_start_kb
from crm2.db.users import get_user_by_nickname, upsert_user

router = Router(name="registration")

# Для совместимости со старыми инлайн-кнопками (если где-то остались)
REG_START = "registration:start"


class RegistrationFSM(StatesGroup):
    nickname = State()
    password = State()
    full_name = State()
    phone = State()
    email = State()
    review = State()


# ───────────────────────────────────────────────────────────────────────────────
# СТАРТ РЕГИСТРАЦИИ (reply-кнопка «Зарегистрироваться» или старый inline)
# ───────────────────────────────────────────────────────────────────────────────
@router.message(F.text.contains("Зарегистрироваться"))
async def start_registration_msg(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationFSM.nickname)
    await message.answer(
        "Введите никнейм (латиница/цифры, без пробелов):",
        reply_markup=guest_start_kb(),
    )


@router.callback_query(F.data == REG_START)
async def start_registration_cb(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationFSM.nickname)
    await cb.message.answer(
        "Введите никнейм (латиница/цифры, без пробелов):",
        reply_markup=guest_start_kb(),
    )
    await cb.answer()


# ───────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ХЕЛПЕРЫ
# ───────────────────────────────────────────────────────────────────────────────
FIELDS_ORDER = ["nickname", "password", "full_name", "phone", "email"]


def _next_missing_field(data: dict) -> str | None:
    for key in FIELDS_ORDER:
        if not (data.get(key) or "").strip():
            return key
    return None


def _mask_pwd(pwd: str | None) -> str:
    pwd = pwd or ""
    return "•" * max(4, len(pwd))


async def _show_review(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = (
        "Проверьте данные:\n"
        f"• Никнейм: {data.get('nickname', '—')}\n"
        f"• Пароль: {_mask_pwd(data.get('password'))}\n"
        f"• ФИО: {data.get('full_name', '—')}\n"
        f"• Телефон: {data.get('phone', '—')}\n"
        f"• Email: {data.get('email', '—')}\n\n"
        "Нажмите на название поля, чтобы исправить.\n"
        "Когда всё верно — нажмите «💾 Сохранить»."
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="Никнейм", callback_data="edit:nickname")
    kb.button(text="Пароль", callback_data="edit:password")
    kb.button(text="ФИО", callback_data="edit:full_name")
    kb.button(text="Телефон", callback_data="edit:phone")
    kb.button(text="Email", callback_data="edit:email")
    kb.button(text="💾 Сохранить", callback_data="reg:save")
    kb.adjust(2, 2, 1)
    await state.set_state(RegistrationFSM.review)
    await message.answer(text, reply_markup=kb.as_markup())


# ───────────────────────────────────────────────────────────────────────────────
# ПОШАГОВО: никнейм → пароль → ФИО → телефон → email → обзор
# ───────────────────────────────────────────────────────────────────────────────
@router.message(RegistrationFSM.nickname)
async def reg_nickname(message: Message, state: FSMContext):
    nickname = (message.text or "").strip()
    if not nickname or " " in nickname:
        await message.answer("Никнейм не должен содержать пробелов. Укажите другой:", reply_markup=guest_start_kb())
        return
    # Проверка на уникальность
    exist = get_user_by_nickname(nickname)
    if exist and exist.get("telegram_id") not in (None, message.from_user.id):
        await message.answer("Такой ник уже занят. Укажите другой никнейм:", reply_markup=guest_start_kb())
        return

    await state.update_data(nickname=nickname)
    await state.set_state(RegistrationFSM.password)
    await message.answer("Введите пароль (не менее 4 символов):", reply_markup=guest_start_kb())


@router.message(RegistrationFSM.password)
async def reg_password(message: Message, state: FSMContext):
    password = (message.text or "").strip()
    if len(password) < 4:
        await message.answer("Короткий пароль. Введите пароль длиной от 4 символов:", reply_markup=guest_start_kb())
        return

    await state.update_data(password=password)
    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:", reply_markup=guest_start_kb())


@router.message(RegistrationFSM.full_name)
async def reg_full_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer("Имя слишком короткое. Повторите, пожалуйста:", reply_markup=guest_start_kb())
        return
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationFSM.phone)
    await message.answer("Введите ваш номер телефона (+7…):", reply_markup=guest_start_kb())


@router.message(RegistrationFSM.phone)
async def reg_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    if not any(ch.isdigit() for ch in phone):
        await message.answer("Похоже, это не номер. Введите телефон ещё раз:", reply_markup=guest_start_kb())
        return
    await state.update_data(phone=phone)
    await state.set_state(RegistrationFSM.email)
    await message.answer("Введите ваш email:", reply_markup=guest_start_kb())


@router.message(RegistrationFSM.email)
async def reg_email(message: Message, state: FSMContext):
    email = (message.text or "").strip()
    if "@" not in email or "." not in email:
        await message.answer("Похоже, это не email. Введите корректный email:", reply_markup=guest_start_kb())
        return
    await state.update_data(email=email)
    await _show_review(message, state)


# ───────────────────────────────────────────────────────────────────────────────
# РЕДАКТИРОВАНИЕ И СОХРАНЕНИЕ (инлайн-кнопки в сообщении со сводкой)
# ───────────────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("edit:"))
async def on_edit_field(cb: CallbackQuery, state: FSMContext):
    field = cb.data.split(":", 1)[1]
    prompts = {
        "nickname": "Введите никнейм (латиница/цифры, без пробелов):",
        "password": "Введите пароль (не менее 4 символов):",
        "full_name": "Введите ваше ФИО:",
        "phone": "Введите ваш номер телефона (+7…):",
        "email": "Введите ваш email:",
    }
    next_state = {
        "nickname": RegistrationFSM.nickname,
        "password": RegistrationFSM.password,
        "full_name": RegistrationFSM.full_name,
        "phone": RegistrationFSM.phone,
        "email": RegistrationFSM.email,
    }[field]
    await state.set_state(next_state)
    await cb.message.answer(prompts[field], reply_markup=guest_start_kb())
    await cb.answer()


@router.callback_query(F.data == "reg:save")
async def on_save(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    missing = _next_missing_field(data)
    if missing:
        await cb.answer("Заполните все поля перед сохранением", show_alert=True)
        await _show_review(cb.message, state)
        return

    # Сохраняем в существующие поля таблицы users — без новых сущностей
    upsert_user(
        telegram_id=cb.from_user.id,
        username=cb.from_user.username,
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        nickname=data.get("nickname", ""),
        password=data.get("password", ""),
        role="user",
        cohort_id=None,
    )
    await state.clear()
    await cb.message.answer("✅ Данные сохранены. Теперь можно войти через «Войти».", reply_markup=guest_start_kb())
    await cb.answer("Сохранено")
