# crm2/handlers/welcome.py
# Назначение: Автоматическое приветствие новых пользователей при первом /start
# Функции:
# - _user_exists - Проверка существования пользователя в БД
# Обработчики:
# - greet_new_user - Поэтическое приветствие для новых пользователей
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import sqlite3
from crm2.db.sqlite import DB_PATH
from crm2.keyboards import guest_start_kb

router = Router(name="welcome")


def _user_exists(tg_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.execute("SELECT 1 FROM users WHERE telegram_id = ? LIMIT 1", (tg_id,))
        return cur.fetchone() is not None


@router.message(CommandStart())
async def greet_new_user(message: Message):
    tg_id = message.from_user.id

    # Если пользователь уже известен — выходим, не дублируем сообщения.
    if _user_exists(tg_id):
        return

    # Поэтическое приветствие для «самого первого шага»
    text = (
        "🌌 *Добро пожаловать в Psytech!*\n\n"
        "Здесь начинается путь — от рассеянности к ясности, "
        "от суеты к собранности, от привычного к свободе.\n\n"
        "Мы бережно соединяем практики внимания и воли, чтобы ты смог "
        "раскрыть внутренний источник силы и устойчивости.\n\n"
        "Выбери первый шаг: войти или зарегистрироваться — и продолжим плавно."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=guest_start_kb())
