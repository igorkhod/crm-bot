# crm2/handlers_schedule.py
from __future__ import annotations

import logging
from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.db.sessions import get_session_by_id, get_upcoming_sessions


schedule_router = Router(name="schedule")


def _fmt_range(start: str, end: str) -> str:
    return f"{start} — {end}" if end and end != start else start


async def send_schedule_keyboard(
    message: Message, limit: int = 5, tg_id: int | None = None
) -> None:
    """
    Показывает блок «Ближайшее занятие» и клавиатуру дат.
    Даты берём с учётом потока (если передан tg_id).
    """
    try:
        sessions = await get_upcoming_sessions(limit=limit, tg_id=tg_id)
    except Exception:
        logging.exception("send_schedule_keyboard failed")
        await message.answer("Ближайших занятий пока нет.")
        return

    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    # Верхний блок: ближайшее занятие
    s0 = sessions[0]
    header = f"{_fmt_range(s0['start_date'], s0['end_date'])} • {s0.get('title', '')}"
    text = f"<b>{escape(header)}</b>"
    ann = s0.get("annotation")
    if ann:
        text += (
            f"\n\n<b>Тема:</b> {escape(s0.get('title', ''))}"
            f"\n<b>Краткое описание:</b> {escape(ann)}"
        )
    await message.answer(text)

    # Клавиатура со списком дат
    kb = InlineKeyboardBuilder()
    for s in sessions:
        label = f"{_fmt_range(s['start_date'], s['end_date'])} • {s.get('title', '')}"
        kb.button(text=label, callback_data=f"session:{s['id']}")
    kb.adjust(1)

    await message.answer("Выберите дату занятия:", reply_markup=kb.as_markup())


@schedule_router.callback_query(F.data.startswith("session:"))
async def on_session_click(callback: CallbackQuery) -> None:
    """Карточка занятия по нажатию на кнопку."""
    try:
        session_id = int(callback.data.split(":", 1)[1])
    except Exception:
        await callback.answer("Некорректный идентификатор", show_alert=True)
        return

    s = await get_session_by_id(session_id)
    if not s:
        await callback.answer("Занятие не найдено", show_alert=True)
        return

    header = f"{_fmt_range(s['start_date'], s['end_date'])} • {s.get('title', '')}"
    ann = s.get("annotation") or "—"
    text = (
        f"<b>{escape(header)}</b>\n\n"
        f"<b>Тема:</b> {escape(s.get('title', ''))}\n"
        f"<b>Краткое описание:</b> {escape(ann)}"
    )
    await callback.message.answer(text)
    await callback.answer()
