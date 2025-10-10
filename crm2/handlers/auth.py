# === Автогенерированный заголовок: crm2/handlers/auth.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: LoginSG
# Функции: _normalize, _is_bcrypt, _check_password, _human_name, _user_role, _bind_telegram_id, _fetch_user_by_credentials, cmd_login, login_nickname, login_password, _show_role_keyboard
# === Конец автозаголовка
# -*- coding: utf-8 -*-
# crm2/handlers/auth.py
# """Хендлеры входа/авторизации."""

from __future__ import annotations  # ← это должно быть первым код-оператором

import asyncio
import hmac
import logging
import re
from typing import Optional

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from crm2.db.core import get_db_connection
from crm2.handlers_schedule import send_nearest_session
# ... остальные стандартные импорты ...
from crm2.keyboards import role_kb  # ← этот импорт переносим НИЖЕ
from crm2.services.users import get_user_by_telegram
from aiogram.filters import Command

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
def _normalize(s: str) -> str:
    """Убираем неразрывные/невидимые пробелы и обрезаем края."""
    if s is None:
        return ""
    s = (s.replace("\u00A0", " ")  # NBSP
         .replace("\uFEFF", "")  # BOM
         .replace("\u200B", "")
         .replace("\u200C", "")
         .replace("\u200D", ""))
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# bcrypt (если в БД $2b$… — сверяем через bcrypt, иначе обычной строкой)
_BCRYPT_RE = re.compile(r"^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}$")


def _is_bcrypt(s: str) -> bool:
    return bool(s) and bool(_BCRYPT_RE.match(s))


def _check_password(db_pw: str, input_pw: str) -> bool:
    raw_db = str(db_pw or "")
    raw_in = str(input_pw or "")

    if _is_bcrypt(raw_db):
        try:
            import bcrypt
            return bcrypt.checkpw(raw_in.encode("utf-8"), raw_db.encode("utf-8"))
        except Exception:
            logging.exception("[AUTH] bcrypt check failed")
            return False

    a = _normalize(raw_db)
    b = _normalize(raw_in)
    try:
        return hmac.compare_digest(a, b)
    except Exception:
        return a == b


def _human_name(user_row: dict) -> str:
    for key in ("full_name", "fio", "name"):
        val = user_row.get(key)
        if val:
            return str(val)
    return str(user_row.get("nickname", "—"))


def _user_role(user_row: dict) -> str:
    return str(user_row.get("role", "user"))


def _bind_telegram_id(user_id: int, tg_id: int) -> None:
    with get_db_connection() as con:
        con.execute(
            """
            UPDATE users
            SET telegram_id = ?
            WHERE id = ?
              AND (telegram_id IS NULL OR telegram_id <> ?)
            """,
            (tg_id, user_id, tg_id),
        )
        con.commit()


def _fetch_user_by_credentials(nickname: str, password: str) -> Optional[dict]:
    nn = _normalize(nickname)
    pw = _normalize(password)
    if not nn or not pw:
        return None

    with get_db_connection() as con:
        cols = {row[1] for row in con.execute("PRAGMA table_info('users')").fetchall()}
        name_col = next((c for c in ("nickname", "login", "username") if c in cols), None)
        if not name_col:
            return None

        con.row_factory = lambda cur, row: {d[0]: row[i] for i, d in enumerate(cur.description)}
        user = con.execute(
            f"SELECT * FROM users WHERE {name_col} = ? COLLATE NOCASE LIMIT 1",
            (nn,),
        ).fetchone()

        if not user:
            # fallback на «нормализованное» сравнение
            for r in con.execute("SELECT * FROM users"):
                if _normalize(str(r.get(name_col) or "")) == nn:
                    user = r
                    break

        if not user:
            return None

        pwd_field = next((k for k in ("password", "pass", "pwd", "passwd", "secret") if k in user), None)
        if not pwd_field:
            return None

        db_pw = str(user.get(pwd_field) or "")
        return user if _check_password(db_pw, password) else None


# -----------------------
# Хендлеры
# -----------------------
# Примерная структура обработчика входа
# @router.message(F.text == "🔐 Войти")
# async def login_handler(message: Message):
#     # После успешной авторизации
#     user = get_user_by_telegram(message.from_user.id)
#     if user and user.get('nickname') and user.get('password'):
#         role = user.get("role", "user")
#         await message.answer(
#             f"Добро пожаловать, {user.get('full_name', 'друг')}! 👋\n"
#             f"Вы вошли с ролью: {role}",
#             reply_markup=role_kb(role)  # Главное меню по роли
#         )


@router.message(F.text == "🔐 Войти")
async def login_handler(message: Message, state: FSMContext):
    """Обработчик кнопки Войти - всегда запускает процесс авторизации"""
    # ВСЕГДА запускаем процесс авторизации, даже если пользователь уже найден
    await state.set_state(LoginSG.nickname)
    await message.answer("Введите ваш никнейм:")


@router.message(LoginSG.nickname)
async def login_nickname(message: Message, state: FSMContext) -> None:
    await state.update_data(nickname=_normalize(message.text or ""))
    await state.set_state(LoginSG.password)
    await message.answer("Введите пароль:")


# Добавьте эту функцию перед login_from_inline
@router.message(Command("login"))
async def cmd_login(message: Message, state: FSMContext) -> None:
    """Обработчик команды /login"""
    await state.set_state(LoginSG.nickname)
    await message.answer("Введите ваш никнейм:")

# И добавьте импорт Command в начало файла:
from aiogram.filters import Command


@router.callback_query(F.data == "login:start")
async def login_from_inline(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cmd_login(cb.message, state)


@router.message(LoginSG.password)
async def login_password(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    nickname = str(data.get("nickname", "")).strip()
    password = _normalize(message.text or "")

    if not nickname or not password:
        await message.answer("Нужно ввести и никнейм, и пароль. Попробуйте ещё раз: /login")
        await state.clear()
        return

    # Авторизация (твоя функция остаётся той же)
    user = await asyncio.to_thread(_fetch_user_by_credentials, nickname, password)
    if not user:
        await message.answer("❌ Неверный никнейм или пароль. Попробуйте ещё раз: /login")
        await state.clear()
        return

    # Универсальный доступ к полям и для dict, и для объекта
    def uget(u, key, default=None):
        return (u.get(key, default) if isinstance(u, dict) else getattr(u, key, default))

    tg_id = message.from_user.id
    full_name = (uget(user, "full_name") or uget(user, "nickname") or "Гость").strip()
    role = (uget(user, "role") or "user").strip()
    cohort = uget(user, "cohort_id") or uget(user, "cohort_id")

    from crm2.keyboards import role_kb

    # Персональное приветствие вместо "Меню"
    lines = [f"Здравствуйте, {full_name}!"]

    role_line = f"Роль: {role}"
    if cohort is not None:
        role_line += f" | Поток: {cohort}"
    lines.append(role_line)

    await message.answer("\n".join(lines), reply_markup=role_kb(role or "user"))

    # Показать ближайшее занятие и клавиатуру расписания
    try:
        await send_nearest_session(message, tg_id=tg_id, limit=5)
    except Exception:
        logging.exception("send_schedule_keyboard failed")

    await state.clear()


async def _show_role_keyboard(message, role: str):
    try:
        await message.answer(f"Ваш кабинет. Роль: {role}", reply_markup=role_kb(role))
    except Exception:
        pass
