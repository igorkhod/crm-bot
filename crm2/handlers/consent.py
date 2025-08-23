# crm2/handlers/consent.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from crm2.db.core import get_db_connection
from aiogram.fsm.context import FSMContext

router = Router(name="consent")

CONSENT_TEXT = (
    "При отправке номера телефона и email при регистрации вы даёте согласие "
    "на обработку персональных данных https://krasnpsytech.ru/ZQFHN32\n"
    "Нажимая на кнопку «Соглашаюсь», вы соглашаетесь получать информационные "
    "сообщения. Отказаться можно в любой момент 👌"
)


def consent_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Соглашаюсь")],
            [KeyboardButton(text="📖 О проекте")],
        ],
        resize_keyboard=True,
    )


def has_consent(tg_id: int) -> bool:
    with get_db_connection() as con:
        row = con.execute(
            "SELECT given FROM consents WHERE telegram_id=?", (tg_id,)
        ).fetchone()
        return bool(row and row[0])


def set_consent(tg_id: int, given: bool = True) -> None:
    with get_db_connection() as con:
        con.execute(
            """
            INSERT INTO consents (telegram_id, given)
            VALUES (?, ?) ON CONFLICT(telegram_id) DO
            UPDATE SET given=excluded.given, ts= CURRENT_TIMESTAMP
            """,
            (tg_id, 1 if given else 0),
        )
        con.commit()


from aiogram.filters import StateFilter

from aiogram import F
from aiogram.fsm.context import FSMContext


@router.message(F.text == "Соглашаюсь")
async def agree(message: Message, state: FSMContext):
    await message.answer("👉 [consent.py] agree() поймал кнопку")
    # ниже можешь временно закомментировать реальную логику,
    # чтобы видеть только маячок
    # set_consent(...); await state.set_state(...); ...


#
# @router.message(F.text == "Соглашаюсь")
# async def agree(message: Message, state: FSMContext):
#     # фиксируем согласие
#     set_consent(message.from_user.id, True)
#
#     # всегда продолжаем регистрацию (если она не шла — начнётся сейчас)
#     from crm2.handlers.registration import RegistrationFSM  # lazy-импорт, чтобы не ловить циклический
#     from aiogram.types import ReplyKeyboardRemove
#
#     await state.set_state(RegistrationFSM.full_name)
#     await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())
