#
# === Файл: crm2/app.py
# Аннотация: модуль CRM, Telegram-бот на aiogram 3.x, доступ к SQLite/ORM, логирование, загрузка конфигурации из .env. Внутри функции: _get_role_from_db, cmd_start, cmd_home, main.
# Добавлено автоматически 2025-08-21 05:43:17

from __future__ import annotations  # ← ДОЛЖНО быть первым (после докстринга/комментариев)

import logging
import os
import sqlite3  # ← добавили

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from dotenv import load_dotenv

from crm2.db.sqlite import DB_PATH  # ← добавили
from crm2.db.sqlite import ensure_schema
from crm2.handlers import auth  # <— новое
from crm2.handlers import registration
from crm2.keyboards import guest_start_kb, role_kb
from crm2.routers import start
from crm2.handlers import info  # ← импорт
from crm2.handlers_schedule import router as schedule_router, send_schedule_keyboard
# from crm2.config import TELEGRAM_TOKEN
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from crm2.handlers import start, consent
from aiogram.fsm.context import FSMContext



def _get_role_from_db(tg_id: int) -> str:
    """Без автоклассификации: читаем роль из БД как есть."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE telegram_id = ?", (tg_id,))
        row = cur.fetchone()
        return (row["role"] if row and row["role"] else "curious")


def _has_consent(tg_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT given FROM consents WHERE telegram_id=?", (tg_id,)
        ).fetchone()
        return bool(row and row[0])

def _set_consent(tg_id: int, given: bool = True) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO consents (telegram_id, given)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET given=excluded.given, ts=CURRENT_TIMESTAMP
            """,
            (tg_id, 1 if given else 0),
        )
        conn.commit()

def _consent_text() -> str:
    return (
        "При отправке номера телефона и email при регистрации вы даёте согласие "
        "на обработку персональных данных https://krasnpsytech.ru/ZQFHN32\n"
        "Нажимая на кнопку «Соглашаюсь», вы соглашаетесь получать информационные "
        "сообщения. Отказаться можно в любой момент 👌"
    )

def _consent_kb():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Соглашаюсь")],
            [KeyboardButton(text="📖 О проекте")],
        ],
        resize_keyboard=True,
    )


load_dotenv()

ensure_schema()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

bot = Bot(
    TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()

dp.include_router(consent.router)
dp.include_router(start.router)
dp.include_router(registration.router)
dp.include_router(auth.router)  # <— новое
dp.include_router(info.router)  # ← подключение
dp.include_router(schedule_router)


@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    # Обнуляем все «следы» прошлых сессий
    await state.clear()

    # Никого не «узнаём»: до входа все — гости
    await message.answer(
        "Добро пожаловать в CRM2!\nВы гость. Выберите действие:",
        reply_markup=guest_start_kb(),  # из твоего keyboards.py (3 кнопки)
    )


# было: отправляли «Спасибо!…»
# @dp.message(F.text == "Соглашаюсь")
# async def agree(message: Message, state: FSMContext):
#     _set_consent(message.from_user.id, True)
#     # избегаем циклического импорта: берём класс FSM внутри функции
#     from crm2.handlers.registration import RegistrationFSM
#     from aiogram.types import ReplyKeyboardRemove
#
#     # сразу продолжаем регистрацию
#     await state.set_state(RegistrationFSM.full_name)
#     await message.answer("Введите ваше ФИО:", reply_markup=ReplyKeyboardRemove())


# @dp.message(F.text == "Соглашаюсь")
# async def agree(message: Message):
#     _set_consent(message.from_user.id, True)
#     await message.answer("app.py Спасибо! Доступ открыт. Нажмите /start, чтобы продолжить.")


@dp.message(F.text.in_({"/home", "Мой кабинет"}))
async def cmd_home(message: Message):
    role = _get_role_from_db(message.from_user.id)  # только чтение
    if role in (None, "", "curious"):
        await message.answer(
            "Вы ещё не авторизованы. Войдите или зарегистрируйтесь:",
            reply_markup=guest_start_kb(),
        )
    else:
        await message.answer(
            f"Ваш кабинет. Роль: {role}",
            reply_markup=role_kb(role),
        )
    # добавить ниже:
    from crm2.handlers_schedule import send_schedule_keyboard
    await message.answer("Нажмите кнопку даты занятия, чтобы открыть тему занятия и краткое описание.")
    await send_schedule_keyboard(message, limit=5, tg_id=message.from_user.id)


async def main() -> None:
    # мягкий запуск: сообщаем админу (если указан)
    #  стартовый логгинг
    import os, logging, hashlib, inspect

    try:
        import crm2.handlers_schedule as hs
        hs_path = inspect.getfile(hs)
        with open(hs_path, "rb") as f:
            hs_sha = hashlib.sha1(f.read()).hexdigest()[:10]
    except Exception:
        hs_path = "<unknown>"
        hs_sha = "<na>"

    logging.warning("[BUILD] COMMIT=%s  BRANCH=%s",
                    os.getenv("RENDER_GIT_COMMIT", "<local>"),
                    os.getenv("RENDER_GIT_BRANCH", "<local>"))
    logging.warning("[DIAG] handlers_schedule=%s sha=%s", hs_path, hs_sha)

    # === конец стартового логгинга

    if ADMIN_ID:
        try:
            await bot.send_message(int(ADMIN_ID), "🚀 Бот запущен! Выберите в меню команду /start для начала работы.")
        except Exception as e:
            logging.error(f"Не удалось написать админу при старте: {e}")

    try:
        # просто стартуем поллинг; на Windows без сигналов
        from crm2.db.auto_migrate import ensure_schedule_schema
        ensure_schedule_schema()  # создаст таблицы и посеет, если пусто
        from crm2.db.auto_migrate import ensure_schedule_schema, apply_topic_overrides

        ensure_schedule_schema()

        apply_topic_overrides({
            "ПТГ-2": {
                "title": "ПТГ на основе метода работы с 4х-мерным пространством",
                "annotation": "Интегральные матрицы для всех уровней живой системы человек за все воплощения; Работа с Родом; Центры сознания; Эндокринные системы для каждого квантового уровня; Уровни искажения схем поведения; Матрицы ДЕЛА; гармонзация души; гармонизация сознания; гармонизация духа; Аспект троичности; Кундалини; Время; Мозг;"
            }
        })

        from crm2.db.auto_migrate import ensure_schedule_schema
        from crm2.db.schedule_loader import sync_schedule_from_files

        ensure_schedule_schema()
        sync_schedule_from_files([
            "schedule_2025_1_cohort.xlsx",
            "schedule_2025_2_cohort.xlsx",
        ])


        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Получен KeyboardInterrupt — завершаем...")
    finally:
        # уведомление админу и корректное закрытие сессии при любом исходе
        if ADMIN_ID:
            try:
                await bot.send_message(int(ADMIN_ID), "⛔ Бот остановлен.")
            except Exception as e:
                logging.error(f"Не удалось написать админу при остановке: {e}")
        await bot.session.close()
        logging.info("Сессия закрыта.")