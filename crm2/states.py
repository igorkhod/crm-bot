# === Файл: crm2/states.py
# Аннотация: модуль CRM, Telegram-бот на aiogram 3.x. Внутри классы: Login.
# Добавлено автоматически 2025-08-21 05:43:17

from aiogram.fsm.state import State, StatesGroup

class Login(StatesGroup):
    nickname = State()
    password = State()