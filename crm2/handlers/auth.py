from __future__ import annotations

import asyncio
import logging
import re
import hmac
import hashlib
from typing import Optional

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
def _normalize(s: str) -> str:
    """
    Убираем невидимые пробелы/маркер BOM и стандартные пробелы по краям.
    Схлопываем повторные пробелы.
    """
    if s is None:
        return ""
    s = (s.replace("\u00A0", " ")   # NBSP
           .replace("\uFEFF", "")   # BOM
           .replace("\u200B", "")   # zero-width
           .replace("\u200C", "")
           .replace("\u200D", ""))
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _to_hex_bytes(s: str) -> str:
    return (s or "").encode("utf-8", "replace").hex()


def _sha256(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _debug_auth_dump(db_pw: str, in_pw: str, who: str = "users.password") -> None:
    """
    Печатаем в логи сырые байты и sha256 пароля из БД и введённого.
    Делает это и для сырых строк, и для нормализованных.
    """
    try:
        db_raw = db_pw or ""
        in_raw = in_pw or ""
        db_norm = _normalize(db_raw)
        in_norm = _normalize(in_raw)

        logging.warning("[AUTH DEBUG] field=%s RAW   len=%d hex=%s sha256=%s",
                        who, len(db_raw), _to_hex_bytes(db_raw), _sha256(db_raw))
        logging.warning("[AUTH DEBUG] input     RAW   len=%d hex=%s sha256=%s",
                        len(in_raw), _to_hex_bytes(in_raw), _sha256(in_raw))
        logging.warning("[AUTH DEBUG] field=%s NORM  len=%d hex=%s sha256=%s",
                        who, len(db_norm), _to_hex_bytes(db_norm), _sha256(db_norm))
        logging.warning("[AUTH DEBUG] input     NORM  len=%d hex=%s sha256=%s",
                        len(in_norm), _to_hex_bytes(in_norm), _sha256(in_norm))
    except Exception:
        logging.exception("[AUTH DEBUG] dump failed")


# --- Поддержка bcrypt и fallback на обычную строку
_BCRYPT_RE = re.compile(r"^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}$")

def _is_bcrypt(s: str) -> bool:
    return bool(s) and bool(_BCRYPT_RE.match(s))

def _check_password(db_pw: str, input_pw: str) -> bool:
    """
    Сравнивает введённый пароль с БД:
      • если в БД bcrypt ($2b$…): bcrypt.checkpw()
      • иначе — обычное сравнение после «очистки» (NBSP/BOM/zero-width)
    """
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
    """
    Аккуратно берём "человеческое" имя пользователя из доступных полей.
    Fallback — nickname.
    """
    for key in ("full_name", "fio", "name"):
        val = user_row.get(key)
        if val:
            return str(val)
    return str(user_row.get("nickname", "—"))


def _user_role(user_row: dict) -> str:
    return str(user_row.get("role", "user"))


def _bind_telegram_id(user_id: int, tg_id: int) -> None:
    """
    Привязываем telegram_id к пользователю, если ещё не привязан или отличается.
    """
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
    """
    Ищем пользователя по нику (регистронезависимо), пароль сверяем корректно (bcrypt/строка).
    Перед сравнением печатаем отладочную информацию: hex/sha256 сырых и нормализованных значений.
    """
    nn = _normalize(nickname)
    pw = _normalize(password)
    if not nn or not pw:
        return None

    with get_db_connection() as con:
        # читаем схему — как называется колонка ника?
        cols = {row[1] for row in con.execute("PRAGMA table_info('users')").fetchall()}
        name_col = next((c for c in ("nickname", "login", "username") if c in cols), None)
        if not name_col:
            return None

        # работать удобнее со словарями
        con.row_factory = lambda cur, row: {d[0]: row[i] for i, d in enumerate(cur.description)}

        # берём пользователя по нику (без учёта регистра)
        user = con.execute(
            f"SELECT * FROM users WHERE {name_col} = ? COLLATE NOCASE LIMIT 1",
            (nn,),
        ).fetchone()

        if not user:
            # fallback: пробегаем всех и сравниваем нормализованные никнеймы
            for r in con.execute("SELECT * FROM users"):
                if _normalize(str(r.get(name_col) or "")) == nn:
                    user = r
                    break

        if not user:
            return None

        # найдём реальное поле с паролем и выведем сравнение/хэши в логи
        pwd_field = next((k for k in ("password", "pass", "pwd", "passwd", "secret") if k in user), None)
        if not pwd_field:
            return None

        db_pw = str(user.get(pwd_field) or "")
        _debug_auth_dump(db_pw, password, who=f"users.{pwd_field}")

        return user if _check_password(db_pw, password) else None


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
    await state.update_data(nickname=_normalize(message.text or ""))
    await state.set_state(LoginSG.password)
    await message.answer("Введите пароль:")


@router.message(LoginSG.password)
async def login_password(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    nickname = str(data.get("nickname", "")).strip()
    password = _normalize(message.text or "")

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

    # Привязываем Telegram ID (мягко)
    tg_id = message.from_user.id
    try:
        await asyncio.to_thread(_bind_telegram_id, int(user["id"]), tg_id)
    except Exception:
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
    await message.answer("Нажмите кнопку даты занятия, чтобы открыть тему занятия и краткое описание.")
    # Важно: передаём tg_id, чтобы расписание было именно для потока пользователя
    await send_schedule_keyboard(message, limit=5, tg_id=tg_id)

    await state.clear()
