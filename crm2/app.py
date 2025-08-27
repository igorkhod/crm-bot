# === Файл: crm2/app.py
# Назначение: Точка входа бота (aiogram v3). Инициализация БД, подключение роутеров, запуск polling.

from __future__ import annotations

import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from dotenv import load_dotenv

from crm2.db.sqlite import DB_PATH, ensure_schema
from crm2.db.migrate_admin import ensure_admin_schema
from crm2.db.auto_migrate import ensure_schedule_schema
from crm2.db.schedule_loader import sync_schedule_from_files

# Роутеры (пользовательские)
from crm2.handlers import start, consent, registration, auth, info

# Общие хэндлеры расписания (клавиатура ближайших занятий)
from crm2.handlers_schedule import router as schedule_router, send_schedule_keyboard

# Админ-панель
from crm2.handlers.admin.panel import router as admin_panel_router
from crm2.handlers.admin.users import router as admin_users_router
from crm2.handlers.admin.schedule import router as admin_schedule_router
from crm2.handlers.admin.logs import router as admin_logs_router
from crm2.handlers.admin.broadcast import router as admin_broadcast_router


# === Утилиты ===============================================================

def _get_role_from_db(tg_id: int) -> str:
    """Читаем роль из БД как есть (без автоклассификации)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE telegram_id = ?", (tg_id,))
        row = cur.fetchone()
        return (row["role"] if row and row["role"] else "curious")


def _is_schedule_text(txt: str) -> bool:
    """Нормализуем «📅 Расписание», 'Расписание', 'schedule'."""
    if not txt:
        return False
    t = txt.replace("📅", "").replace("🗓", "").strip().lower()
    return t in {"расписание", "schedule"}


# === Инициализация окружения и логирования =================================

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не задан в окружении (.env)")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# === Бот/диспетчер ==========================================================

bot = Bot(TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# === Роутеры ================================================================

dp.include_router(consent.router)
dp.include_router(start.router)
dp.include_router(registration.router)
dp.include_router(auth.router)
dp.include_router(info.router)

# общий роутер расписания (коллбэки карточек и т.п.)
dp.include_router(schedule_router)

# админ-подсекции
dp.include_router(admin_panel_router)
dp.include_router(admin_users_router)
dp.include_router(admin_schedule_router)
dp.include_router(admin_logs_router)
dp.include_router(admin_broadcast_router)


# === Хэндлеры верхнего уровня (кнопки/команды) =============================

# Кнопка «📅 Расписание» / текст «Расписание»
@dp.message(F.text.func(_is_schedule_text))
async def open_schedule_by_text(message: Message):
    await send_schedule_keyboard(message, limit=5, tg_id=message.from_user.id)

# Команда /schedule на всякий случай
@dp.message(Command("schedule"))
async def open_schedule_by_cmd(message: Message):
    await send_schedule_keyboard(message, limit=5, tg_id=message.from_user.id)

# Кабинет пользователя + показ расписания
@dp.message(F.text.in_({"/home", "Мой кабинет"}))
async def cmd_home(message: Message):
    role = _get_role_from_db(message.from_user.id)
    if role in (None, "", "curious"):
        from crm2.keyboards import guest_start_kb
        await message.answer(
            "Вы ещё не авторизованы. Войдите или зарегистрируйтесь:",
            reply_markup=guest_start_kb(),
        )
    else:
        from crm2.keyboards import role_kb
        await message.answer(f"Ваш кабинет. Роль: {role}", reply_markup=role_kb(role))

    await message.answer("Нажмите кнопку даты занятия, чтобы открыть тему занятия и краткое описание.")
    await send_schedule_keyboard(message, limit=5, tg_id=message.from_user.id)


# === Точка входа ===========================================================

async def main() -> None:
    # Диагностика сборки
    import hashlib, inspect
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

    # Схемы БД
    ensure_schema()           # users/consents
    ensure_admin_schema()     # admin-таблицы
    ensure_schedule_schema()  # topics/session_days/events/healings

    # Импорт расписания из XLSX (лежат в корне репозитория на Render)
    sync_schedule_from_files([
        "schedule_2025_1_cohort.xlsx",
        "schedule_2025_2_cohort.xlsx",
    ])

    # Старт бота
    if ADMIN_ID:
        try:
            await bot.send_message(int(ADMIN_ID), "🚀 Бот запущен!")
        except Exception as e:
            logging.error(f"Не удалось написать админу при старте: {e}")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt — завершаем...")
    finally:
        if ADMIN_ID:
            try:
                await bot.send_message(int(ADMIN_ID), "⛔ Бот остановлен.")
            except Exception as e:
                logging.error(f"Не удалось написать админу при остановке: {e}")
        await bot.session.close()
        logging.info("Сессия закрыта.")
