from aiogram.fsm.state import State, StatesGroup

class Login(StatesGroup):
    nickname = State()
    password = State()
