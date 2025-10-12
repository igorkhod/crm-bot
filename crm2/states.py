# === Автогенерированный заголовок: crm2/states.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: Login
# Функции: —
# === Конец автозаголовка
#
# === Файл: crm2/states.py
# Аннотация: FSM состояния для процесса авторизации в Telegram-боте
from aiogram.fsm.state import State, StatesGroup

class Login(StatesGroup):
    nickname = State()
    password = State()