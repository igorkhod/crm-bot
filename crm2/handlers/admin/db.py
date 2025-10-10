# crm2/handlers/admin/db.py
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "admin:db")
async def admin_db(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer("🗄 Раздел работы с базой данных в разработке")