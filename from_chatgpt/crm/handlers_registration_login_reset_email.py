from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from crm.db import get_user_by_nickname
from crm.keyboards import get_role_keyboard
from crm.services import verify_user_password

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
    """
    1) Берём ник из сообщения.
    2) Сразу проверяем в БД, существует ли такой пользователь.
    3) Если НЕ существует — мягко просим ввести ник ещё раз (и предлагаем регистрацию).
    4) Если существует — сохраняем ник в FSM и переходим к запросу пароля.
    """
    nickname = message.text.strip()

    # Проверяем наличие пользователя до запроса пароля
    db_user = await get_user_by_nickname(nickname)
    if db_user is None:
        # Клавиатура с двумя вариантами: повторить ввод ника или перейти к регистрации
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [types.KeyboardButton(text="🔁 Ввести ник ещё раз")],
            [types.KeyboardButton(text="🆕 Зарегистрироваться")]
        ])
        await message.answer(
            "Пользователь с таким никнеймом не найден. "
            "Проверьте написание и попробуйте снова, либо зарегистрируйтесь.",
            reply_markup=kb
        )
        # Остаёмся в состоянии ожидания ника
        await state.set_state(LoginStates.waiting_for_nickname)
        return

    # Ник валиден — сохраняем и запрашиваем пароль
    await state.update_data(nickname=nickname)
    await message.answer("Введите ваш пароль:")
    await state.set_state(LoginStates.waiting_for_password)


@router.message(F.text == "🔁 Ввести ник ещё раз")
async def retry_nickname(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш никнейм:")
    await state.set_state(LoginStates.waiting_for_nickname)


@router.message(F.text == "🆕 Зарегистрироваться")
async def go_register(message: types.Message, state: FSMContext):
    await message.answer("Введите желаемый никнейм для регистрации:")
    await state.set_state(LoginStates.waiting_for_nickname)


@router.message(LoginStates.waiting_for_password)
async def login_password_received(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    nickname = user_data.get("nickname")
    password = message.text.strip()

    db_user = await get_user_by_nickname(nickname)
    if db_user is None:
        await message.answer("Пользователь с таким никнеймом не найден. Попробуйте снова.")
        # await state.clear()
        # было: await state.clear()
        # стало: запоминаем в FSM данные о сессии пользователя
        await state.update_data(role=db_user["role"], nickname=db_user["nickname"], user_id=db_user.get("id"))
        # снимаем текущий state, но данные оставляем
        await state.set_state(None)

        await message.answer(
            f"Добро пожаловать, {db_user['full_name']}!",
            reply_markup=get_role_keyboard(role=db_user["role"], is_authenticated=True)
        )

        return
    ok = await verify_user_password(nickname, password)
    if not ok:
        # Клавиатура: повторить ввод или сменить пароль
        retry_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [types.KeyboardButton(text="🔁 Повторить пароль")],
            [types.KeyboardButton(text="🔐 Сменить пароль")]
        ])
        await message.answer("Введён неправильный пароль.", reply_markup=retry_kb)
        # Оставляем nickname в состоянии и снова ждём пароль
        await state.set_state(LoginStates.waiting_for_password)
        return

    await state.clear()
    await message.answer(f"Добро пожаловать, {db_user['full_name']}!",
                         reply_markup=get_role_keyboard(role=db_user["role"], is_authenticated=True))


registration_router = router

@router.message(F.text == "Выйти")
async def logout(message: types.Message, state: FSMContext):
    # Полностью очищаем состояние и показываем гостевое меню
    await state.clear()
    await message.answer("Вы вышли из аккаунта.", reply_markup=get_role_keyboard(is_authenticated=False))

# На всякий случай — ответ на /logout
@router.message(F.text == "/logout")
async def logout_cmd(message: types.Message, state: FSMContext):
    await logout(message, state)

