
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from crm2.db.sessions import get_upcoming_sessions, get_session_by_id
from crm2.keyboards.schedule import build_schedule_keyboard, format_range

logger = logging.getLogger(__name__)
router = Router(name="schedule")


async def send_schedule_keyboard(message: Message, *, limit: int = 5, tg_id: int | None = None) -> None:
    """
    Renders:
      1) "Ближайшее занятие: DD.MM.YYYY — DD.MM.YYYY • CODE"
      2) Inline keyboard with all available upcoming dates (date range + code).
    """
    try:
        sessions = get_upcoming_sessions(limit=limit, tg_id=tg_id) or []
    except Exception:
        logger.exception("send_schedule_keyboard failed")
        await message.answer("Не удалось получить расписание. Попробуйте позже.")
        return

    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    # First line: "Ближайшее занятие:"
    first = sessions[0]
    code = (first.get("topic_code") or "").strip()
    first_line = f"Ближайшее занятие: {format_range(first['start_date'], first['end_date'])}"
    if code:
        first_line += f" • {code}"
    await message.answer(first_line)

    # Keyboard with all items
    await message.answer(
        "Выберите дату занятия:",
        reply_markup=build_schedule_keyboard(sessions),
    )


# --- Callbacks ---

@router.callback_query(F.data.startswith("session:"))
async def on_session_click(callback: CallbackQuery):
    raw = callback.data or ""
    try:
        sid = int(raw.split(":", 1)[1])
    except Exception:
        await callback.answer("Некорректный идентификатор занятия", show_alert=True)
        return

    try:
        row = get_session_by_id(sid)
    except Exception:
        logger.exception("get_session_by_id failed")
        row = None

    if not row:
        await callback.message.answer("Не удалось найти запись :(")
        await callback.answer()
        return

    title = (row.get("title") or "").strip() or "Без темы"
    ann = (row.get("annotation") or "").strip() or "—"
    label = format_range(row.get("start_date"), row.get("end_date"))
    code = (row.get("topic_code") or "").strip()

    text = f"<b>{label}</b>"
    if code:
        text += f"\n<b>Код:</b> {code}"
    text += f"\n<b>Тема:</b> {title}\n<b>Краткое описание:</b> {ann}"

    await callback.message.answer(text)
    await callback.answer()


# Export alias for compatibility with app.py
schedule_router = router
__all__ = ['schedule_router', 'router', 'send_schedule_keyboard']
