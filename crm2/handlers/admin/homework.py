# crm2/handlers/admin/homework.py
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "admin:homework")
async def admin_homework(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer("📚 Раздел домашних заданий в разработке")

# Функция для входа из panel.py
async def admin_homework_entry(message: Message):
    await message.answer("📚 Панель управления домашними заданиями")