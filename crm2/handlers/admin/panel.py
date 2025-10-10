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


@router.message(F.text == "⚙️ Админ")
async def handle_admin_button(message: Message):
    """Обработчик кнопки Админ из главного меню"""
    u = get_user_by_telegram(message.from_user.id)
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
    kb.button(text="⬅️ В главное меню", callback_data="admin:back_main")
    kb.adjust(2, 2, 2)
    return kb


async def open_admin_menu(message: Message) -> None:
    await message.answer("⚙️ Админ-панель", reply_markup=_admin_kb().as_markup())


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    u = get_user_by_telegram(message.from_user.id)
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


# УДАЛИТЕ ЭТОТ ОБРАБОТЧИК - ОН ДУБЛИРУЕТСЯ С attendance.py
# @router.callback_query(F.data == "admin:attendance")
# async def go_attendance(cq: CallbackQuery):
#     await cq.answer()
#     # Передаём управление модулю посещаемости
#     from crm2.handlers.admin_attendance import admin_attendance_entry
#     await admin_attendance_entry(cq)


@router.callback_query(F.data == "admin:homework")
async def go_homework(cq: CallbackQuery):
    await cq.answer()
    from crm2.handlers.admin.homework import admin_homework_entry
    await admin_homework_entry(cq.message)


@router.callback_query(F.data == "admin:schedule")
async def go_schedule(cq: CallbackQuery):
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