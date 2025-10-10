# crm2/handlers/admin/panel.py
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.services.users import get_user_by_telegram

logger = logging.getLogger(__name__)
router = Router(name="admin_panel")

# ─────────── клавиатуры ───────────
def _admin_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗓 Расписание", callback_data="admin:schedule")
    kb.button(text="✅ Посещаемость", callback_data="admin:attendance")
    kb.button(text="📚 Домашние задания", callback_data="admin:homework")
    kb.button(text="👥 Пользователи", callback_data="admin:users")
    kb.button(text="🗄 База", callback_data="admin:db")
    kb.button(text="⬅️ В главное меню", callback_data="admin:back_main")
    kb.adjust(2, 2, 2)
    return kb

# ─────────── публичная функция, которую импортирует admin_attendance ───────────
async def open_admin_menu(message: Message) -> None:
    await message.answer("⚙️ Админ-панель", reply_markup=_admin_kb().as_markup())

# /admin и кнопка из главного меню
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    u = get_user_by_telegram(message.from_user.id)
    if not u or (u.get("role") != "admin"):
        await message.answer("⛔️ Доступ только для админов.")
        return
    await open_admin_menu(message)

# Кнопки из админ-панели
@router.callback_query(F.data == "admin:back_main")
async def back_to_main(cq: CallbackQuery):
    # возвращаем в главное меню (не в гостевое)
    from crm2.handlers.main_menu import open_main_menu  # локальный импорт, чтобы избежать циклов
    await cq.message.delete()
    await open_main_menu(cq.message)
    await cq.answer()

@router.callback_query(F.data == "admin:attendance")
async def go_attendance(cq: CallbackQuery):
    await cq.answer()
    # Передаём управление модулю посещаемости
    from crm2.handlers.admin_attendance import show_attendance_entry  # локально, чтобы не ловить циклический импорт
    await show_attendance_entry(cq.message)

# ========== ПАТЧ 1: Подключение модуля домашних заданий ==========
# ДО (строки 47-49):
# @router.callback_query(F.data == "admin:homework")
# async def go_homework(cq: CallbackQuery):
#     await cq.answer()
#     await cq.message.answer("Раздел «Домашние задания» в разработке.")

# ПОСЛЕ:
@router.callback_query(F.data == "admin:homework")
async def go_homework(cq: CallbackQuery):
    await cq.answer()
    # Импортируем обработчик из FSM-версии
    from crm2.handlers.admin_homework import admin_homework_entry
    await admin_homework_entry(cq.message)

@router.callback_query(F.data == "admin:schedule")
async def go_schedule(cq: CallbackQuery):
# ========== КОНЕЦ ПАТЧА 1 ==========

    await cq.answer()
    await cq.message.answer("Раздел «Расписание» в разработке.")

@router.callback_query(F.data == "admin:users")
async def go_users(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer("Раздел «Пользователи» в разработке.")

@router.callback_query(F.data == "admin:db")
async def go_db(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer("Раздел «База» в разработке.")