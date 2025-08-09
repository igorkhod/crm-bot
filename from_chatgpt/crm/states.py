
from aiogram.fsm.state import StatesGroup, State


class LoginStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_password = State()


class RegistrationStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_password = State()


class PasswordResetStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_new_password = State()
