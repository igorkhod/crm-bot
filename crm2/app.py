# === Файл: crm2/app.py
# Назначение: Точка входа бота (aiogram v3). Инициализация БД, подключение роутеров, запуск polling.

from __future__ import annotations

import hashlib
import inspect
import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

from crm2.db.auto_migrate import ensure_schedule_schema  # только схемы, без импорта
from crm2.db.migrate_admin import ensure_admin_schema
from crm2.db.sqlite import DB_PATH, ensure_schema
from crm2.handlers import about as about_router
from crm2.handlers import help as help_router
# Роутеры (пользовательские)
from crm2.handlers import start, consent, registration, auth, info
from crm2.handlers import welcome as welcome_router
from crm2.handlers.admin.broadcast import router as admin_broadcast_router
from crm2.handlers.admin.logs import router as admin_logs_router
# Админ-подсекции
from crm2.handlers.admin.panel import router as admin_panel_router
from crm2.handlers.admin.schedule import router as admin_schedule_router
from crm2.handlers.admin.users import router as admin_users_router
# Общие хэндлеры расписания (клавиатура ближайших занятий)
from crm2.handlers_schedule import router as schedule_router, send_schedule_keyboard, show_info_menu


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
# приглушаем «обычный сетевой шум»
logging.getLogger("aiogram.client.session.aiohttp").setLevel(logging.WARNING)
logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
logging.getLogger("aiohttp.helpers").setLevel(logging.WARNING)

# === Бот/диспетчер ==========================================================

# Dispatcher можно создать на уровне модуля
dp = Dispatcher()

# === Роутеры ================================================================
dp.include_router(consent.router)
dp.include_router(welcome_router.router)  # авто-приветствие новых /start
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
dp.include_router(help_router.router)
dp.include_router(about_router.router)


# === Хэндлеры верхнего уровня (кнопки/команды) =============================

# Кнопка «📅 Расписание» / текст «Расписание»
@dp.message(F.text.func(_is_schedule_text))
async def open_schedule_by_text(message: Message):
    await show_info_menu(message)


# Команда /schedule
@dp.message(Command("schedule"))
async def open_schedule_by_cmd(message: Message):
    await show_info_menu(message)


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

    # Схемы БД (users/admin/schedule)
    ensure_schema()
    ensure_admin_schema()
    ensure_schedule_schema()

    # Автозагрузка расписания (по требованию)
    if os.getenv("CRM_SYNC_SCHEDULE_ON_START") == "1":
        from crm2.db.schedule_loader import sync_schedule_from_files
        files = ["schedule_2025_1_cohort.xlsx", "schedule_2025_2_cohort.xlsx"]
        try:
            affected = sync_schedule_from_files(files)
            logging.info("[SCHEDULE IMPORT] on start: affected rows=%s", affected)
        except Exception as e:
            logging.exception("Schedule import on start failed: %s", e)

    # --- создаём HTTP-сессию и бота ПОД живым event-loop’ом ---
    # ВАЖНО: для aiogram v3 timeout должен быть числом (секунды), не ClientTimeout
    session = AiohttpSession(timeout=70)  # читаем чуть дольше, чем polling_timeout

    bot = Bot(
        TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    # Старт бота
    if ADMIN_ID:
        try:
            await bot.send_message(int(ADMIN_ID), "🚀 Бот запущен!")
        except Exception as e:
            logging.error(f"Не удалось написать админу при старте: {e}")

    try:
        await dp.start_polling(
            bot,
            polling_timeout=60,  # синхрон с session.timeout (70)
            allowed_updates=None,
            drop_pending_updates=False,
        )
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
