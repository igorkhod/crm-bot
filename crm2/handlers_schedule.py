from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from html import escape

from crm2.keyboards import build_schedule_keyboard, format_range
from crm2.db import get_upcoming_sessions, get_session_by_id  # см. примечание ниже

schedule_router = Router()

async def send_schedule_keyboard(message: Message, *, limit: int = 5):
    sessions = await get_upcoming_sessions(limit=limit)
    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return
    await message.answer("Выберите дату занятия:", reply_markup=build_schedule_keyboard(sessions))

@schedule_router.callback_query(F.data.startswith("session:"))
async def on_session_click(callback: CallbackQuery):
    session_id = int(callback.data.split(":", 1)[1])
    s = await get_session_by_id(session_id)
    if not s:
        await callback.answer("Занятие не найдено", show_alert=True)
        return

    header = f"{format_range(s['start_date'], s['end_date'])} • {s.get('topic_code') or '—'}"
    title = s.get("title") or "Без названия"
    annotation = s.get("annotation") or "—"

    text = (
        f"<b>{escape(header)}</b>\n\n"
        f"<b>Тема:</b> {escape(title)}\n"
        f"<b>Краткое описание:</b> {escape(annotation)}"
    )

    sessions = await get_upcoming_sessions(limit=5)
    await callback.message.edit_text(
        text,
        reply_markup=build_schedule_keyboard(sessions),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()
