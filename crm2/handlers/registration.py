# crm2/handlers/registration.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import logging

router = Router()
log = logging.getLogger(__name__)


# ─────────────────────────── FSM ───────────────────────────

class RegistrationFSM(StatesGroup):
    full_name = State()


# ─────────────────────────── Вспомогательные функции ───────────────────────────

def _save_full_name_to_db(telegram_id: int, full_name: str) -> bool:
    """
    Пытаемся сохранить ФИО в users:
    1) Сначала — через crm2.db.users, если там есть подходящие функции.
    2) Если нет — прямым запросом к SQLite (/var/data/crm.db).
    Возвращает True при успехе, иначе False.
    """
    # Попытка №1: через модуль crm2.db.users (если есть)
    try:
        from crm2.db.users import get_user_by_tg, upsert_user_fields  # type: ignore
        try:
            user = get_user_by_tg(telegram_id)
        except TypeError:
            # get_user_by_tg мог быть sync/async; если вдруг async — игнор и идём дальше
            user = None

        # Универсальная "апсертовая" функция, если есть
        if 'upsert_user_fields' in dir():
            upsert_user_fields(telegram_id, {"full_name": full_name})  # type: ignore
            return True

        # Если нет upsert, попробуем обновить существующего или создать нового
        from crm2.db.users import update_user_fields, create_user_min  # type: ignore
        if user:
            update_user_fields(telegram_id, {"full_name": full_name})  # type: ignore
            return True
        else:
            create_user_min(telegram_id, {"full_name": full_name})  # type: ignore
            return True
    except Exception as e:
        log.debug("users.py path not available or failed: %r", e)

    # Попытка №2: прямой доступ к SQLite
    try:
        import sqlite3
        DB_PATH = "/var/data/crm.db"
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        # Проверим, есть ли такой пользователь
        cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET full_name = ? WHERE telegram_id = ?", (full_name, telegram_id))
        else:
            # создаём минимальную запись
            cur.execute(
                "INSERT INTO users (telegram_id, full_name, role) VALUES (?, ?, COALESCE((SELECT 'user'), 'user'))",
                (telegram_id, full_name),
            )
        con.commit()
        con.close()
        return True
    except Exception as e:
        log.warning("SQLite save full_name failed: %r", e)
        return False


# ─────────────────────────── Точка входа ───────────────────────────

async def start_registration(message: Message, state: FSMContext) -> None:
    """
    Начинаем регистрацию. ВНИМАНИЕ: здесь больше НЕТ показа/проверки согласия —
    согласие выводится в start.py перед вызовом этой функции.
    """
    await state.clear()
    await state.set_state(RegistrationFSM.full_name)
    await message.answer("Введите ваше ФИО:")


# ─────────────────────────── Шаги регистрации ───────────────────────────

@router.message(RegistrationFSM.full_name)
async def reg_full_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()
    if not full_name:
        await message.answer("Пожалуйста, введите ФИО текстом.")
        return

    await state.update_data(full_name=full_name)

    tg_id = message.from_user.id
    ok = _save_full_name_to_db(tg_id, full_name)

    if ok:
        await message.answer(f"Спасибо, {full_name}! ✨\n"
                             f"Профиль обновлён. Продолжим позже настройку кабинета.")
    else:
        await message.answer(f"Спасибо, {full_name}! ✨\n"
                             f"Не удалось сохранить данные автоматически — сообщите администратору, пожалуйста.")

    # Здесь можно добавить следующий шаг анкеты (никнейм/телефон/почта и т.д.)
    # Пока завершаем сценарий:
    await state.clear()
