from __future__ import annotations

import asyncio
import logging
from typing import Optional, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from crm2.db.core import get_db_connection
from crm2.db.sessions import get_user_stream_title_by_tg
from crm2.handlers_schedule import send_schedule_keyboard
from crm2.keyboards import role_kb


router = Router(name="auth")


# -----------------------
# FSM для входа в систему
# -----------------------
class LoginSG(StatesGroup):
    nickname = State()
    password = State()


# -----------------------
# Вспомогательные функции
# -----------------------
def _fetch_user_by_credentials(nickname: str, password: str) -> Optional[dict]:
    """
    Возвращает dict с данными пользователя по паре (nickname, password)
    или None, если не найден.
    """
    with get_db_connection() as con:
        con.row_factory = lambda cur, row: {d[0]: row[i] for i, d in enumerate(cur.description)}
        cur = con.execute(
            """
            SELECT *
            FROM users
            WHERE nickname = ? AND password = ?
            LIMIT 1
            """,
            (nickname, password),
        )
        row = cur.fetchone()
        return row


def _bind_telegram_id(user_id: int, tg_id: int) -> None:
    """Привязывает telegram_id к пользователю, если он ещё не привязан или отличается."""
    with get_db_connection() as con:
        con.execute(
            """
            UPDATE users
            SET telegram_id = ?
            WHERE id = ?
            """,
            (tg_id, user_id),
        )
        con.commit()


def _human_name(user_row: dict) -> str:
    """
    Аккуратно берём "человеческое" имя пользователя из доступных полей.
    Fallback — nickname.
    """
    for key in ("full_name", "fio", "name"):
        if key in user_row and user_row[key]:
            return str(user_row[key])
    return str(user_row.get("nickname", "—"))


def _user_role(user_row: dict) -> str:
    return str(user_row.get("role", "user"))


# -----------------------
# Хендлеры
# -----------------------
@router.message(F.text.in_({"/login", "🔐 Войти"}))
async def cmd_login(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LoginSG.nickname)
    await message.answer("Введите ваш никнейм:")


@router.message(LoginSG.nickname)
async def login_nickname(message: Message, state: FSMContext) -> None:
    await state.update_data(nickname=message.text.strip())
    await state.set_state(LoginSG.password)
    await message.answer("Введите пароль:")


@router.message(LoginSG.password)
async def login_password(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    nickname = str(data.get("nickname", "")).strip()
    password = (message.text or "").strip()

    if not nickname or not password:
        await message.answer("Нужно ввести и никнейм, и пароль. Попробуйте ещё раз: /login")
        await state.clear()
        return

    # --- проверяем пользователя в БД
    user = await asyncio.to_thread(_fetch_user_by_credentials, nickname, password)
    if not user:
        await message.answer("❌ Неверный никнейм или пароль. Попробуйте ещё раз: /login")
        await state.clear()
        return

    # Привязываем Telegram ID
    tg_id = message.from_user.id
    try:
        await asyncio.to_thread(_bind_telegram_id, int(user["id"]), tg_id)
    except Exception:  # pragma: no cover
        logging.exception("failed to bind telegram id")

    # Готовим приветствие
    full_name = _human_name(user)
    role = _user_role(user)

    # Узнаём поток пользователя (id + удобная подпись)
    stream_id, stream_title = await asyncio.to_thread(get_user_stream_title_by_tg, tg_id)

    text = (
        "✅ Вход выполнен.\n"
        f"Вы вошли как: {full_name}\n"
        f"Роль: {role}"
    )
    if stream_title:
        text += f"\nПоток: {stream_title}"

    # Сообщение + главное меню по роли
    await message.answer(text, reply_markup=role_kb(role))

    # Подсказка и расписание (ТОЛЬКО один раз)
    await message.answer(
        "Нажмите кнопку даты занятия, чтобы открыть тему занятия и краткое описание."
    )
    # Важно: передаём tg_id, чтобы расписание было именно для потока пользователя
    await send_schedule_keyboard(message, limit=5, tg_id=tg_id)

    await state.clear()
