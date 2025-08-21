#
# === Файл: crm2/handlers/auth.py
# Аннотация: модуль CRM, хендлеры и маршрутизация событий Telegram, Telegram-бот на aiogram 3.x, доступ к SQLite/ORM, логирование. Внутри классы: LoginFSM, функции: build_main_menu, get_db, fetch_user_by_nickname, touch_last_seen, attach_telegram_if_empty....
# Добавлено автоматически 2025-08-21 05:43:17

# crm2/handlers/auth.py
import logging  # если не импортирован вверху
import sqlite3
from passlib.hash import bcrypt
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from crm2.keyboards import role_kb
from crm2.db.sqlite import DB_PATH


router = Router()

# ---------- FSM ----------
class LoginFSM(StatesGroup):
    nickname = State()
    password = State()


def build_main_menu(role: str) -> ReplyKeyboardMarkup:
    """
    Главное меню:
      • для admin: добавляем строку '🛠 Панель администратора'
      • для остальных ролей: без админки
    """
    rows = [
        [KeyboardButton(text="ℹ️ Информация")],
        [KeyboardButton(text="🏠 Меню")],
    ]
    if (role or "").lower() == "admin":
        rows.insert(0, [KeyboardButton(text="🛠 Панель администратора")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ---------- DB helpers ----------

# ---------- DB helpers (BEGIN) ----------
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_user_by_nickname(nickname: str) -> dict | None:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, telegram_id, full_name, nickname, password AS password_hash, role, cohort_id
              FROM users
             WHERE nickname = ?
             LIMIT 1
            """,
            (nickname,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

def touch_last_seen(telegram_id: int) -> None:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET last_seen = datetime('now') WHERE telegram_id = ?",
            (telegram_id,),
        )
        conn.commit()

def attach_telegram_if_empty(user_id: int, tg_id: int) -> None:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
               SET telegram_id = ?
             WHERE id = ?
               AND telegram_id IS NULL
            """,
            (tg_id, user_id),
        )
        conn.commit()
# ---------- DB helpers (END) ----------

# ---------- Handlers ----------
# запускаем логин: кнопка «Войти», текст «войти», или команда /login
@router.message(F.text == "🔐 Войти")
@router.message(F.text.func(lambda t: isinstance(t, str) and "войти" in t.lower()))
@router.message(Command("login"))
async def start_login(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(LoginFSM.nickname)
    await message.answer("Введите ваш никнейм:", reply_markup=ReplyKeyboardRemove())


@router.message(LoginFSM.nickname)
async def login_nickname(message: Message, state: FSMContext):
    nickname = (message.text or "").strip()
    if len(nickname) < 3:
        await message.answer("Ник слишком короткий. Попробуйте ещё раз:")
        return

    user = fetch_user_by_nickname(nickname)
    if not user:
        await message.answer("❌ Пользователь с таким ником не найден. Проверьте ник или зарегистрируйтесь.")
        return

    await state.update_data(user_id=user["id"], nickname=nickname)
    await state.set_state(LoginFSM.password)
    await message.answer("Введите пароль:")


@router.message(LoginFSM.password)
async def login_password(message: Message, state: FSMContext):
    data = await state.get_data()
    nickname = data.get("nickname") or ""

    user = fetch_user_by_nickname(nickname)
    if not user:
        await message.answer("❌ Пользователь не найден. Начните вход заново: /login")
        await state.clear()
        return

    pwd = (message.text or "").strip()
    hash_ = user.get("password_hash") or ""

    # проверяем хэш
    try:
        ok = bool(hash_) and bcrypt.verify(pwd, hash_)
    except Exception:
        ok = False

    if not ok:
        await message.answer("❌ Неверный пароль. Попробуйте ещё раз или введите /login заново.")
        return

    # защита от «чужого» tg аккаунта: если в записи другой telegram_id — предупредим
    tg_id = message.from_user.id
    u_tg = user.get("telegram_id")
    if u_tg is not None and u_tg != "" and u_tg != tg_id:
        await state.clear()
        await message.answer(
            "⚠️ Этот ник уже привязан к другому Telegram-аккаунту. Обратитесь к администратору."
        )
        return

    # привязываем tg_id, если пустой; обновляем last_seen
    attach_telegram_if_empty(user["id"], tg_id)
    touch_last_seen(tg_id)

    role = user.get("role") or "curious"

    logging.info(f"login: nickname={user.get('nickname')}, tg_id={tg_id}, role_in_db={role}")
    await state.clear()
    await message.answer(
        f"✅ Вход выполнен.\nВы вошли как: {user.get('full_name') or nickname}\nРоль: {role}",
        reply_markup=role_kb(role)
    )
    from crm2.handlers_schedule import send_schedule_keyboard
    await message.answer("Нажмите кнопку даты занятия, чтобы открыть тему занятия и краткое описание.")
    await send_schedule_keyboard(message, limit=5)

    # txt = next_training_text_for_user(message.from_user.id)
    # if txt:
    #     await message.answer(txt)