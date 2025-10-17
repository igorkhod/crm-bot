# crm2/handlers/registration.py
# Назначение: Полный цикл регистрации и редактирования профиля пользователя с FSM
# Классы:
# - EditField - FSM состояния для редактирования полей профиля (nickname, password, full_name, phone, email)
# Функции:
# - _edit_kb - Клавиатура выбора поля для редактирования
# - _cohort_inline_kb - Инлайн-клавиатура выбора потока с визуализацией текущего
# - _user_card - Форматирование карточки пользователя для отображения
# Обработчики:
# - show_fix_card_cmd - Старт редактирования по команде /fix
# - show_fix_card_text - Старт редактирования по текстовым командам
# - edit_nickname/save_nickname - Редактирование никнейма (FSM)
# - edit_password/save_password - Редактирование пароля (FSM)
# - edit_full_name/save_full_name - Редактирование ФИО (FSM)
# - edit_phone/save_phone - Редактирование телефона (FSM)
# - edit_email/save_email - Редактирование email (FSM)
# - choose_cohort - Выбор потока обучения
# - set_cohort_cb - Сохранение выбранного потока через callback
# - back_from_inline - Возврат из инлайн-меню
# новое описание:
# crm2/handlers/registration.py
# Назначение: Полный цикл регистрации и редактирования профиля пользователя с FSM
# Классы:
# - EditField - FSM состояния для редактирования полей профиля (nickname, password, full_name, phone, email)
# Функции:
# - _edit_kb - Клавиатура выбора поля для редактирования
# - _cohort_inline_kb - Инлайн-клавиатура выбора потока с визуализацией текущего
# - _user_card - Форматирование карточки пользователя для отображения
# Обработчики:
# - show_fix_card_cmd - Старт редактирования по команде /fix
# - show_fix_card_text - Старт редактирования по текстовым командам
# - edit_nickname/save_nickname - Редактирование никнейма (FSM)
# - edit_password/save_password - Редактирование пароля (FSM)
# - edit_full_name/save_full_name - Редактирование ФИО (FSM)
# - edit_phone/save_phone - Редактирование телефона (FSM)
# - edit_email/save_email - Редактирование email (FSM)
# - choose_cohort - Выбор потока обучения
# - set_cohort_cb - Сохранение выбранного потока через callback
# - back_from_inline - Возврат из инлайн-меню
from __future__ import annotations

from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from crm2.services.users import (
    get_user_by_telegram,
    set_plain_user_field_by_tg,
    upsert_participant_by_tg,
)

router = Router(name="registration")

# ───────────────────────── FSM ─────────────────────────
class EditField(StatesGroup):
    nickname = State()
    password = State()
    full_name = State()
    phone = State()
    email = State()

# ───────────────────────── Клавиатуры ─────────────────────────
def _edit_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Никнейм"), KeyboardButton(text="Пароль")],
        [KeyboardButton(text="ФИО"), KeyboardButton(text="Телефон")],
        [KeyboardButton(text="Email"), KeyboardButton(text="Поток")],
        [KeyboardButton(text="💾 Сохранить")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def _cohort_inline_kb(current: Optional[int]) -> InlineKeyboardMarkup:
    def label(n: int) -> str:
        return f"Поток {n}" + (" ✅" if current == n else "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label(1), callback_data="reg:set_cohort:1")],
        [InlineKeyboardButton(text=label(2), callback_data="reg:set_cohort:2")],
        [InlineKeyboardButton(
            text="Сбросить (нет потока)" + (" ✅" if current is None else ""),
            callback_data="reg:set_cohort:0"
        )],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="reg:back")],
    ])

def _user_card(u: dict) -> str:
    cohort = u.get("cohort_id")
    cohort_line = f"Поток: {cohort if cohort else 'не указан'}"
    return (
        "• Никнейм: {nickname}\n"
        "• Пароль: {password_mask}\n"
        "• ФИО: {full_name}\n"
        "• Телефон: {phone}\n"
        "• Email: {email}\n"
        f"• {cohort_line}"
    ).format(
        nickname=u.get("nickname") or "—",
        password_mask="******" if u.get("password") else "—",
        full_name=u.get("full_name") or "—",
        phone=u.get("phone") or "—",
        email=u.get("email") or "—",
    )

# ───────────────────────── Старт карточки правок ─────────────────────────
# ВАЖНО: избегаем `Command(...) | F...` — делаем два отдельных хендлера

@router.message(Command("fix"))
async def show_fix_card_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    u = await get_user_by_telegram(message.from_user.id) or {}
    await message.answer("Выберите действие:", reply_markup=_edit_kb())
    await message.answer(_user_card(u))

@router.message(F.text.func(lambda t: t and t.lower() in {"исправить регистрацию", "исправить", "править"}))
async def show_fix_card_text(message: Message, state: FSMContext) -> None:
    await state.clear()
    u = await get_user_by_telegram(message.from_user.id) or {}
    await message.answer("Выберите действие:", reply_markup=_edit_kb())
    await message.answer(_user_card(u))

# ───────────────────────── Текстовые поля ─────────────────────────
@router.message(F.text == "Никнейм")
async def edit_nickname(message: Message, state: FSMContext):
    await state.set_state(EditField.nickname)
    await message.answer("Введите *новый никнейм*:", parse_mode="Markdown")

@router.message(EditField.nickname, F.text)
async def save_nickname(message: Message, state: FSMContext):
    set_plain_user_field_by_tg(message.from_user.id, "nickname", message.text.strip())
    await state.clear()
    u = await get_user_by_telegram(message.from_user.id) or {}
    await message.answer("Готово. Никнейм обновлён.")
    await message.answer(_user_card(u), reply_markup=_edit_kb())

@router.message(F.text == "Пароль")
async def edit_password(message: Message, state: FSMContext):
    await state.set_state(EditField.password)
    await message.answer("Введите *новый пароль*:", parse_mode="Markdown")

@router.message(EditField.password, F.text)
async def save_password(message: Message, state: FSMContext):
    set_plain_user_field_by_tg(message.from_user.id, "password", message.text.strip())
    await state.clear()
    u = await get_user_by_telegram(message.from_user.id) or {}
    await message.answer("Готово. Пароль обновлён.")
    await message.answer(_user_card(u), reply_markup=_edit_kb())

@router.message(F.text == "ФИО")
async def edit_full_name(message: Message, state: FSMContext):
    await state.set_state(EditField.full_name)
    await message.answer("Введите *ФИО*:", parse_mode="Markdown")

@router.message(EditField.full_name, F.text)
async def save_full_name(message: Message, state: FSMContext):
    set_plain_user_field_by_tg(message.from_user.id, "full_name", message.text.strip())
    await state.clear()
    u = await get_user_by_telegram(message.from_user.id) or {}
    await message.answer("Готово. ФИО обновлено.")
    await message.answer(_user_card(u), reply_markup=_edit_kb())

@router.message(F.text == "Телефон")
async def edit_phone(message: Message, state: FSMContext):
    await state.set_state(EditField.phone)
    await message.answer("Введите *телефон*:", parse_mode="Markdown")

@router.message(EditField.phone, F.text)
async def save_phone(message: Message, state: FSMContext):
    set_plain_user_field_by_tg(message.from_user.id, "phone", message.text.strip())
    await state.clear()
    u = await get_user_by_telegram(message.from_user.id) or {}
    await message.answer("Готово. Телефон обновлён.")
    await message.answer(_user_card(u), reply_markup=_edit_kb())

@router.message(F.text == "Email")
async def edit_email(message: Message, state: FSMContext):
    await state.set_state(EditField.email)
    await message.answer("Введите *email*:", parse_mode="Markdown")

@router.message(EditField.email, F.text)
async def save_email(message: Message, state: FSMContext):
    set_plain_user_field_by_tg(message.from_user.id, "email", message.text.strip())
    await state.clear()
    u = await get_user_by_telegram(message.from_user.id) or {}
    await message.answer("Готово. Email обновлён.")
    await message.answer(_user_card(u), reply_markup=_edit_kb())

# ───────────────────────── Поток ─────────────────────────
@router.message(F.text == "Поток")
async def choose_cohort(message: Message):
    u = await get_user_by_telegram(message.from_user.id) or {}
    current = u.get("cohort_id")
    await message.answer(
        "Выберите ваш поток:",
        reply_markup=_cohort_inline_kb(current if isinstance(current, int) else None)
    )

@router.callback_query(F.data.startswith("reg:set_cohort:"))
async def set_cohort_cb(cq: CallbackQuery):
    _, _, value = cq.data.split(":", 2)
    tg_id = cq.from_user.id
    cohort_id = int(value)
    set_plain_user_field_by_tg(tg_id, "cohort_id", None if cohort_id == 0 else cohort_id)
    await upsert_participant_by_tg(tg_id, None if cohort_id == 0 else cohort_id)
    u = await get_user_by_telegram(tg_id) or {}
    await cq.message.edit_text("Поток обновлён.\n\n" + _user_card(u))
    await cq.answer("Сохранено ✅")

@router.callback_query(F.data == "reg:back")
async def back_from_inline(cq: CallbackQuery):
    await cq.message.delete()
    await cq.answer()
