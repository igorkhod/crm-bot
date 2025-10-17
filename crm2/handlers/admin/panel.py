from __future__ import annotations

import logging

# crm2/handlers/admin/panel.py
# Назначение: Главное меню админ-панели с навигацией по разделам
# Функции:
# - _admin_kb - Создание клавиатуры главного меню админ-панели
# - open_admin_menu - Открытие главного меню админ-панели
# - back_to_main - Возврат в главное меню бота
# Обработчики:
# - handle_admin_button - Обработчик кнопки "⚙️ Админ" из главного меню
# - cmd_admin - Обработчик команды /admin
# - go_homework - Переход в раздел домашних заданий
# - go_schedule - Переход в раздел расписания (заглушка)
# - go_users - Переход в раздел пользователей (заглушка)
# - go_db - Переход в раздел базы данных (заглушка)
#handlers/
#├── admin/                    # Актуальные обработчики админ-панели
#│   ├── attendance.py        # ✅ ОБНОВЛЕН - использует users.cohort_id
#│   ├── panel.py            # Главное меню
#│   ├── schedule.py         # Просмотр расписания
#│   ├── users.py            # Просмотр пользователей
#│   └── logs.py             # Логи рассылок
#├── admin_attendance.py      # 🗑️ УДАЛИТЬ (дубликат)
#├── admin_db.py             # Диагностика БД
#├── admin_db_doctor.py      # Расширенная диагностика БД
#├── admin_homework.py       # Управление домашними заданиями
#├── broadcast.py            # Массовые рассылки
#└── chatgpt.py              # Проверка статуса ChatGPT
# новое описание
# panel.py
# Путь: crm2/handlers/admin/panel.py
# Назначение: Главное меню админ-панели с навигацией по разделам
# Функции:
#
# _admin_kb - Создание клавиатуры главного меню админ-панели
#
# open_admin_menu - Открытие главного меню админ-панели
#
# back_to_main - Возврат в главное меню бота
# Обработчики (не включаем в список функций, но в назначении упомянули, что это обработчики)


from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.services.users import get_user_by_telegram

logger = logging.getLogger(__name__)
router = Router(name="admin_panel")


@router.message(F.text == "⚙️ Админ")
async def handle_admin_button(message: Message):
    """Обработчик кнопки Админ из главного меню"""
    u = await get_user_by_telegram(message.from_user.id)
    if not u or u.get("role") != "admin":
        await message.answer("⛔️ Доступ только для админов.")
        return
    await open_admin_menu(message)


# ─────────── клавиатуры ───────────
def _admin_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗓 Расписание", callback_data="admin:schedule")
    kb.button(text="✅ Посещаемость", callback_data="admin:attendance")
    kb.button(text="📚 Домашние задания", callback_data="admin:homework")
    kb.button(text="👥 Пользователи", callback_data="admin:users")
    kb.button(text="🗄 База", callback_data="admin:db")
    kb.button(text="📊 Логи рассылок", callback_data="admin:logs")
    kb.button(text="🤖 ChatGPT статус", callback_data="admin:chatgpt")
    kb.button(text="⬅️ В главное меню", callback_data="admin:back_main")
    kb.adjust(2, 2, 2, 2)
    return kb


async def open_admin_menu(message: Message) -> None:
    await message.answer("⚙️ Админ-панель", reply_markup=_admin_kb().as_markup())


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    u = await get_user_by_telegram(message.from_user.id)
    if not u or (u.get("role") != "admin"):
        await message.answer("⛔️ Доступ только для админов.")
        return
    await open_admin_menu(message)


@router.callback_query(F.data == "admin:back_main")
async def back_to_main(cq: CallbackQuery):
    from crm2.keyboards import role_kb
    await cq.message.delete()
    await cq.message.answer("Главное меню", reply_markup=role_kb("admin"))
    await cq.answer()


@router.callback_query(F.data == "admin:attendance")
async def go_attendance(cq: CallbackQuery):
    await cq.answer()
    from crm2.handlers.admin.attendance import admin_attendance_entry
    await admin_attendance_entry(cq)


@router.callback_query(F.data == "admin:homework")
async def go_homework(cq: CallbackQuery):
    await cq.answer()
    from crm2.handlers.admin.admin_homework import admin_homework_entry
    await admin_homework_entry(cq)


@router.callback_query(F.data == "admin:schedule")
async def go_schedule(cq: CallbackQuery):
    # Убрали await cq.answer() - он будет в schedule_menu
    from crm2.handlers.admin.schedule import schedule_menu
    await schedule_menu(cq)  # Передаем cq вместо cq.message


@router.callback_query(F.data == "admin:users")
async def go_users(cq: CallbackQuery):
    await cq.answer()
    from crm2.handlers.admin.users import admin_users_entry
    await admin_users_entry(cq)


@router.callback_query(F.data == "admin:db")
async def go_db(cq: CallbackQuery):
    await cq.answer()
    from crm2.handlers.admin.db import admin_db
    await admin_db(cq.message)


@router.callback_query(F.data == "admin:logs")
async def go_logs(cq: CallbackQuery):
    await cq.answer()
    from crm2.handlers.admin.logs import logs_overview
    await logs_overview(cq.message)


@router.callback_query(F.data == "admin:chatgpt")
async def go_chatgpt(cq: CallbackQuery):
    await cq.answer()
    from crm2.handlers.admin.chatgpt import admin_chatgpt_entry
    await admin_chatgpt_entry(cq.message)