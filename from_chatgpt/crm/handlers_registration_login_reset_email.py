
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# from crm.database import get_user_by_nickname
# from crm.keyboards import get_role_keyboard
from crm.db import get_user_by_nickname
from crm.keyboards import get_role_keyboard

router = Router()


class LoginStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_password = State()


@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Добро пожаловать! Пожалуйста, выберите действие:",
                         reply_markup=get_role_keyboard(is_authenticated=False))
    await state.clear()


@router.message(F.text.contains("Войти"))
async def login_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш никнейм:")
    await state.set_state(LoginStates.waiting_for_nickname)


@router.message(LoginStates.waiting_for_nickname)
async def login_nickname_received(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    await state.update_data(nickname=nickname)
    await message.answer("Введите ваш пароль:")
    await state.set_state(LoginStates.waiting_for_password)


@router.message(LoginStates.waiting_for_password)
async def login_password_received(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    nickname = user_data.get("nickname")
    password = message.text.strip()

    db_user = await get_user_by_nickname(nickname)
    if db_user is None:
        await message.answer("Пользователь с таким никнеймом не найден. Попробуйте снова.")
        await state.clear()
        return

    if db_user["password"] != password:
        await message.answer("Неверный пароль. Попробуйте снова.")
        await state.clear()
        return

    await state.clear()
    await message.answer(f"Добро пожаловать, {db_user['full_name']}!",
                         reply_markup=get_role_keyboard(role=db_user["role"], is_authenticated=True))

registration_router = router