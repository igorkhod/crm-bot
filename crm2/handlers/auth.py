# crm2/handlers/auth.py
# auth.py
# Путь: crm2/handlers/auth.py
# Назначение: Аутентификация пользователей (логин, проверка пароля, управление сессией)
# Классы:
# AuthStates - Состояния FSM для процесса аутентификации (waiting_username, waiting_password)
# Функции:
# start_with_auth - Начало работы (гостевое меню аутентификации)
# show_guest_auth_menu - Показ меню аутентификации для гостя
# handle_auth_start - Обработчик начала аутентификации (кнопка 'Войти')
# handle_username_input - Обработчик ввода username
# handle_password_input - Обработчик ввода пароля и аутентификации
# authenticate_user - Функция аутентификации пользователя (проверка логина/пароля)
# show_main_menu - Показ главного меню после успешной аутентификации
# is_authenticated - Проверка аутентификации пользователя
# get_user_session - Получение сессии пользователя
# cmd_login - Алиас для handle_auth_start
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hcode

from crm2.services.users import get_user_by_nickname, update_user_telegram_id

# Храним сессии пользователей (в продакшене используйте БД)
user_sessions = {}


class AuthStates(StatesGroup):
    waiting_username = State()
    waiting_password = State()


router = Router()


async def start_with_auth(message: Message, state: FSMContext) -> None:
    """Начало работы - всегда гостевой экран аутентификации"""
    user_id = message.from_user.id

    # Сбрасываем сессию при каждом старте
    user_sessions[user_id] = {'authenticated': False, 'username': None}

    # Сбрасываем состояние FSM
    await state.clear()

    # Показываем гостевое меню аутентификации
    await show_guest_auth_menu(message)


async def show_guest_auth_menu(message: Message) -> None:
    """Показывает меню аутентификации для гостя"""
    auth_keyboard = [[KeyboardButton(text="Войти")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard=auth_keyboard,
        resize_keyboard=True,
        input_field_placeholder="Нажмите 'Войти' для начала"
    )

    welcome_text = (
        "🔐 Добро пожаловать в Psytech CRM!\n\n"
        "Здесь начинается ваш путь из дисциплины в свободу.\n"
        "Для доступа к системе необходимо войти.\n\n"
        "Нажмите 'Войти' для начала аутентификации"
    )

    await message.answer(welcome_text, reply_markup=reply_markup)


async def handle_auth_start(message: Message, state: FSMContext) -> None:
    """Обработчик начала процесса аутентификации (кнопка 'Войти')"""
    # Устанавливаем состояние "ожидание username"
    await state.set_state(AuthStates.waiting_username)

    await message.answer(
        "👤 Вход в систему\n\n"
        "Пожалуйста, введите ваш никнейм:"
    )


async def handle_username_input(message: Message, state: FSMContext) -> None:
    """Обработчик ввода username"""
    username = message.text.strip()

    # Сохраняем username и переходим к ожиданию пароля
    await state.update_data(username=username)
    await state.set_state(AuthStates.waiting_password)

    await message.answer(
        "🔒 Вход в системе\n\n"
        f"Пользователь: {hcode(username)}\n"
        "Пожалуйста, введите ваш пароль:"
    )

    # async def handle_password_input(message: Message, state: FSMContext) -> None:
    """Обработчик ввода пароля и аутентификации"""


async def handle_password_input(message: Message, state: FSMContext) -> None:
    """Обработчик ввода пароля и аутентификации"""
    user_id = message.from_user.id
    password = message.text.strip()

    # Получаем username из состояния
    user_data = await state.get_data()
    username = user_data.get('username')

    if not username:
        await handle_auth_start(message, state)
        return

    # Аутентифицируем пользователя
    auth_result = await authenticate_user(username, password)

    if auth_result['success']:
        # Успешная аутентификация - обновляем telegram_id в БД
        user_db_id = auth_result['user_data']['user_id']
        await update_user_telegram_id(user_db_id, user_id)

        user_sessions[user_id] = {
            'authenticated': True,
            'username': username,
            'user_data': auth_result['user_data']
        }

        # Сбрасываем состояние
        await state.clear()

        await message.answer(
            f"✅ Вход выполнен успешно, {hcode(username)}!\n\n"
            "Добро пожаловать в систему Psytech CRM!"
        )

        # Показываем главное меню
        await show_main_menu(message)
    else:
        # Ошибка аутентификации
        await message.answer(
            "❌ Ошибка входа!\n\n"
            "Неверный никнейм или пароль.\n"
            "Попробуйте еще раз."
        )
        # Возвращаем к началу аутентификации
        await handle_auth_start(message, state)


from crm2.utils.password_utils import verify_and_upgrade_password
from crm2.services.users import update_user_password


async def authenticate_user(username: str, password: str) -> dict:
    """Функция аутентификации пользователя через БД с проверкой хеша"""
    try:
        # Ищем пользователя в БД по nickname
        user = await get_user_by_nickname(username)

        logging.info(f"🔍 Поиск пользователя: {username}")
        logging.info(f"📋 Найден пользователь: {bool(user)}")

        if user:
            stored_password = user.get('password', '')
            logging.info(f"🔐 Хеш пароля из БД: {stored_password}")
            logging.info(f"📝 Введенный пароль: {password}")

            # Используем правильную проверку пароля с поддержкой bcrypt
            success, new_hash = verify_and_upgrade_password(password, stored_password, user.get('id'))

            if success:
                logging.info("✅ Аутентификация успешна")

                # Если пароль был в plain text и нужно обновить хеш
                if new_hash != stored_password:
                    await update_user_password(user.get('id'), new_hash)
                    logging.info("🔄 Пароль обновлен с plain text на bcrypt")

                return {
                    'success': True,
                    'user_data': {
                        'username': user.get('nickname'),
                        'role': user.get('role', 'user'),
                        'user_id': user.get('id')
                    }
                }
            else:
                logging.info("❌ Неверный пароль")

        return {'success': False}
    except Exception as e:
        logging.error(f"Auth error: {e}")
        return {'success': False}


async def show_main_menu(message: Message) -> None:
    """Показывает главное меню после успешной аутентификации"""
    user_id = message.from_user.id
    user_data = user_sessions.get(user_id, {})

    # Создаем кнопки с использованием KeyboardButton
    menu_keyboard = [
        [
            KeyboardButton(text="📅 Расписание"),
            KeyboardButton(text="📚 Материалы")
        ],
        [
            KeyboardButton(text="👤 Личный кабинет"),
            KeyboardButton(text="🤖 ИИ-агенты")
        ],
        [
            KeyboardButton(text="⚙️ Админ"),
            KeyboardButton(text="📊 Посещение")
        ]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=menu_keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел..."
    )

    username = user_data.get('username', 'Неизвестный')
    role = user_data.get('user_data', {}).get('role', 'user')

    await message.answer(
        f"🏠 Главное меню\n\n"
        f"Пользователь: {hcode(username)}\n"
        f"Роль: {hcode(role)}",
        reply_markup=reply_markup
    )


def is_authenticated(user_id: int) -> bool:
    """Проверяет, аутентифицирован ли пользователь"""
    return user_sessions.get(user_id, {}).get('authenticated', False)


def get_user_session(user_id: int):
    """Возвращает сессию пользователя"""
    return user_sessions.get(user_id)


# Алиас для обратной совместимости
async def cmd_login(message: Message, state: FSMContext) -> None:
    """Алиас для handle_auth_start для совместимости со старым кодом"""
    await handle_auth_start(message, state)


# Регистрируем обработчики в router
router.message.register(start_with_auth, Command("start"))
router.message.register(handle_auth_start, F.text == "Войти")
router.message.register(handle_username_input, AuthStates.waiting_username)
router.message.register(handle_password_input, AuthStates.waiting_password)
