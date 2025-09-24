# crm2/handlers/admin/panel.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from crm2.keyboards import admin_panel_kb
from crm2.handlers.admin_attendance import (
    show_attendance_menu,
    show_homework_menu,
)

router = Router()

# команда/кнопка, которая открывает админ-панель
@router.message(F.text.in_({"Админ", "/admin"}))
async def open_admin_panel(message: Message):
    await message.answer("Админ-панель:", reply_markup=admin_panel_kb())

# кнопка в панели: Посещаемость
@router.callback_query(F.data == "adm:attendance")
async def _open_attendance(cb: CallbackQuery):
    await show_attendance_menu(cb.message)
    await cb.answer()

# кнопка в панели: Домашние задания
@router.callback_query(F.data == "adm:homework")
async def _open_homework(cb: CallbackQuery):
    await show_homework_menu(cb.message)
    await cb.answer()
