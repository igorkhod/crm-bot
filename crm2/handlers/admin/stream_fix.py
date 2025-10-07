# crm2/handlers/admin/streams_fix.py
from __future__ import annotations

import logging
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.services.participants import (
    users_missing_stream,
    get_streams,
    upsert_participant_stream,
)

router = Router()

ADMIN_ID = os.getenv("ADMIN_ID")
try:
    ADMIN_ID_INT = int(ADMIN_ID) if ADMIN_ID else None
except Exception:
    ADMIN_ID_INT = None


def _is_admin(message: Message) -> bool:
    return bool(ADMIN_ID_INT) and message.from_user.id == ADMIN_ID_INT


def _assign_kb(user_id: int):
    kb = InlineKeyboardBuilder()
    streams = get_streams() or [(1, "Поток 1"), (2, "Поток 2")]
    for sid, title in streams:
        kb.button(text=title, callback_data=f"admin:setstream:{user_id}:{sid}")
    kb.adjust(2)
    return kb


@router.message(F.text.lower().in_({"admin_streams", "/admin_streams"}))
async def show_missing_streams(message: Message):
    if not _is_admin(message):
        return
    rows = users_missing_stream(limit=100)
    if not rows:
        await message.answer("🎉 Все пользователи уже привязаны к потокам.")
        return

    await message.answer(
        f"Нужно назначить поток для {len(rows)} пользователей.\n"
        "Нажимайте кнопки под каждым пользователем."
    )
    for r in rows:
        uline = r["full_name"] or (r["username"] and "@" + r["username"]) or f"id={r['user_id']}"
        text = f"👤 {uline}\n• user_id={r['user_id']}  tg_id={r['telegram_id']}\n• cohort_id={r['cohort_id']}  stream_id=—"
        await message.answer(text, reply_markup=_assign_kb(r["user_id"]).as_markup())


@router.callback_query(F.data.startswith("admin:setstream:"))
async def admin_set_stream(cq: CallbackQuery):
    if not ADMIN_ID_INT or cq.from_user.id != ADMIN_ID_INT:
        await cq.answer("Только админ.", show_alert=True)
        return

    try:
        _, _, user_id_s, stream_id_s = cq.data.split(":")
        user_id = int(user_id_s)
        stream_id = int(stream_id_s)
    except Exception:
        await cq.answer("Некорректные данные", show_alert=True)
        return

    upsert_participant_stream(user_id, stream_id)
    await cq.message.edit_text(cq.message.text + f"\n\n✅ Назначен поток: {stream_id}")
    await cq.answer("Готово")
