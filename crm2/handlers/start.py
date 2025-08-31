# crm2/handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext

from crm2.db.users import get_user_by_tg
from crm2.keyboards.main_menu import role_kb

# Мягкие зависимости (если модулей нет — просто пропустим)
from crm2.handlers import welcome as welcome_handlers
from crm2.handlers import registration as registration_handlers
from crm2.handlers.registration import RegistrationFSM

# ✳️ Импортируем функции согласия (исправляет ошибки has_consent / consent_kb)
from crm2.handlers.consent import has_consent, consent_kb

router = Router()

CONSENT_URL = "https://www.krasnpsytech.ru/FCKrhyrM72sim"
CONSENT_CB = "consent:agree"   # callback-data для кнопки согласия


# ─────────────────────────── Клавиатуры ───────────────────────────

def guest_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Войти"), KeyboardButton(text="📝 Зарегистрироваться")],
            [KeyboardButton(text="ℹ️ О проекте")],
        ],
        resize_keyboard=True
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Открыть документ", url=CONSENT_URL)],
        [InlineKeyboardButton(text="✅ Да, согласен", callback_data=CONSENT_CB)],
    ])


# ─────────────────────────── Вьюшки ───────────────────────────

async def send_guest_welcome(message: Message) -> None:
    """Экран гостя: приветствие + выбор действия."""
    if hasattr(welcome_handlers, "show_welcome"):
        await welcome_handlers.show_welcome(message)
    else:
        await message.answer(
            "Добро пожаловать в Psytech! 🌌 Здесь начинается путь из дисциплины в свободу.\n"
            "Ниже — важные шаги для запуска."
        )
    await message.answer("Вы гость. Выберите действие:", reply_markup=guest_menu())


async def send_main_menu(message: Message, role: str) -> None:
    await message.answer(f"Главное меню (ваша роль: {role})", reply_markup=role_kb(role))


async def show_consent(message: Message, state: FSMContext) -> None:
    """
    Единственная точка показа согласия (anti-dup).
    Ставим флаг в FSM, чтобы не присылать текст повторно.
    """
    data = await state.get_data()
    if data.get("consent_prompted"):
        return

    await state.update_data(consent_prompted=True)
    await message.answer(
        "Для продолжения требуется согласие на обработку персональных данных.\n"
        "Ознакомьтесь с документом и подтвердите согласие.",
        reply_markup=consent_keyboard()
    )


# ─────────────────────────── Хэндлеры ───────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """/start: гость → экран гостя, пользователь → главное меню."""
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)

    if not user or (user.get("role") or "user").strip().lower() == "guest":
        await send_guest_welcome(message)
        return

    role = (user.get("role") or "user").strip().lower()
    await send_main_menu(message, role)


async def start_guest_onboarding(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id

    # 1) Тёплое приветствие
    await message.answer(
        "Добро пожаловать в Psytech! 🌌 Здесь начинается путь из дисциплины в свободу.\n"
        "Ниже — важные шаги для запуска."
    )

    # 2) Если согласия нет — показываем ОДНО сообщение с кнопкой «Открыть документ»
    #    и просим нажать «Соглашаюсь» (клавиатура из consent_kb()).
    if not has_consent(tg_id):
        await message.answer(
            "Для продолжения требуется согласие на обработку персональных данных.\n"
            "Ознакомьтесь с документом и подтвердите согласие.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[  # только ссылка на документ
                InlineKeyboardButton(text="📑 Открыть документ", url=CONSENT_URL)
            ]])
        )
        # Показываем только клавиатуру «Соглашаюсь» (без дополнительного текста).
        await message.answer(" ", reply_markup=consent_kb())
        return

    # 3) Если согласие уже есть — сразу начинаем регистрацию
    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == CONSENT_CB)
async def consent_agreed(cb: CallbackQuery, state: FSMContext):
    """Пользователь подтвердил согласие — запускаем регистрацию."""
    await cb.answer("Спасибо! Согласие получено.")
    await state.update_data(consent_prompted=False)  # сбросили флаг
    msg: Message = cb.message

    # Запускаем регистрацию
    if hasattr(registration_handlers, "start_registration"):
        await registration_handlers.start_registration(msg, state)
        return
    if hasattr(registration_handlers, "cmd_registration"):
        await registration_handlers.cmd_registration(msg)
        return

    await msg.answer("Запуск регистрации… (обратитесь к администратору, если шаг не появился)")


@router.message(F.text.in_({"↩️ Главное меню", "Главное меню"}))
async def back_to_main(message: Message) -> None:
    tg_id = message.from_user.id
    user = get_user_by_tg(tg_id)
    role = (user.get("role") if user else "user") or "user"
    await send_main_menu(message, role)
