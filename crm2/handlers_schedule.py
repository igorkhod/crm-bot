# crm2/handlers_schedule.py
from __future__ import annotations

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.db.sessions import (
    get_upcoming_sessions,
    get_session_by_id,
)

# Роутер этого модуля
schedule_router = Router(name="schedule")


def _row_text(s: dict) -> str:
    """Текст на кнопке: YYYY-MM-DD • Название темы."""
    return f"{s.get('date','')} • {s.get('title','')}".strip(" •")


async def send_schedule_keyboard(message: Message, *, limit: int = 5, tg_id: int | None = None) -> None:
    """Отправить блок с «Ближайшее занятие» + список следующих дат."""
    sessions = await asyncio.to_thread(get_upcoming_sessions, limit=limit, tg_id=tg_id)

    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    # 1) Отдельная кнопка «Ближайшее занятие»
    nearest = sessions[0]
    kb_nearest = InlineKeyboardBuilder()
    kb_nearest.button(text=_row_text(nearest), callback_data=f"session:{nearest['id']}")
    kb_nearest.adjust(1)
    await message.answer("Ближайшее занятие:", reply_markup=kb_nearest.as_markup())

    # 2) Кнопки остальных дат (без дубля ближайшей)
    others = sessions[1:] if len(sessions) > 1 else []
    if others:
        kb = InlineKeyboardBuilder()
        for s in others:
            kb.button(text=_row_text(s), callback_data=f"session:{s['id']}")
        kb.adjust(1)
        await message.answer("Выберите дату занятия:", reply_markup=kb.as_markup())


@schedule_router.callback_query(F.data.startswith("session:"))
async def on_session_click(callback: CallbackQuery):
    """Открыть тему/краткое описание по нажатию на кнопку даты."""
    try:
        sid = int(callback.data.split(":", 1)[1])
    except Exception:
        await callback.answer("Некорректный идентификатор.", show_alert=True)
        return

    s = await asyncio.to_thread(get_session_by_id, sid)
    if not s:
        await callback.answer("Занятие не найдено.", show_alert=True)
        return

    text = (
        f"<b>{s['date']}</b>\n"
        f"<b>Тема:</b> {s.get('title','—')}"
    )
    await callback.message.answer(text)
    await callback.answer()
