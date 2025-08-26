# crm2/handlers/start.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from crm2.handlers.consent import has_consent, consent_kb, CONSENT_TEXT

router = Router(name="start")

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Без согласия — только «Соглашаюсь» и «📖 О проекте»
    if not has_consent(message.from_user.id):
        await message.answer(CONSENT_TEXT, reply_markup=consent_kb())
        return

    # До входа с паролем — вы гость
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="✏️ Регистрация"), KeyboardButton(text="📖 О проекте")],
        ],
        resize_keyboard=True,
    )
    await message.answer("Добро пожаловать в CRM2!\nВы гость. Выберите действие:", reply_markup=kb)
