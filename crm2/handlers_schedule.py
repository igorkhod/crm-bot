from __future__ import annotations

import logging
from html import escape

from aiogram import Router
from aiogram.enums.parse_mode import ParseMode

from crm2.db import get_upcoming_sessions, get_session_by_id
from crm2.keyboards import build_schedule_keyboard, format_range
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

schedule_router = Router()


def _short_from_annotation(s: str | None) -> str:
    if not s:
        return ""
    s = s.strip()
    # берём первую «фразу» до разделителя
    for sep in (";", "•", "—", "-", "\n"):
        i = s.find(sep)
        if i > 3:
            return s[:i].strip()
    return s


# async def send_schedule_keyboard(message: Message, *, limit: int = 5) -> None:
async def send_schedule_keyboard(message: Message, *, limit: int = 5, include_nearest: bool = True) -> None:
    try:
        sessions = await get_upcoming_sessions(limit=limit)
    except Exception:
        logger.exception("send_schedule_keyboard failed")
        await message.answer("Расписание временно недоступно. Попробуйте позже.")
        return

    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    # 1) Кнопка "Ближайшее занятие" — только при первом показе
    if include_nearest:
        first = sessions[0]
        first_text = f"{format_range(first['start_date'], first['end_date'])} • {first.get('topic_code') or '—'}"
        nearest_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=first_text, callback_data=f"session:{first['id']}")]]
        )
        await message.answer("Ближайшее занятие:", reply_markup=nearest_kb)
        rest = sessions[1:]
    else:
        rest = sessions

    # 2) Остальные даты (если есть)
    if rest:
        await message.answer(
            "Выберите дату занятия:",
            reply_markup=build_schedule_keyboard(rest),
        )



@schedule_router.callback_query(lambda c: c.data and c.data.startswith("session:"))
async def on_session_click(callback: CallbackQuery) -> None:
    try:
        session_id = int(callback.data.split(":", 1)[1])
        s = await get_session_by_id(session_id)
        if not s:
            await callback.answer("Занятие не найдено", show_alert=True)
            return

        header = f"{format_range(s['start_date'], s['end_date'])} • {s.get('topic_code') or '—'}"

        display_title = (
            (s.get("title") or "").strip()
            or _short_from_annotation(s.get("annotation"))
            or (s.get("topic_code") or "").strip()
            or "Тема уточняется"
        )
        display_annotation = (s.get("annotation") or "").strip()

        lines = [f"<b>{escape(header)}</b>", ""]
        lines.append(f"<b>Тема:</b> {escape(display_title)}")
        if display_annotation:
            lines.append(f"<b>Краткое описание:</b> {escape(display_annotation)}")
        text = "\n".join(lines)

        # 1) Заменяем исходное сообщение на карточку (без клавиатуры)
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML)

        # 2) Кладём клавиатуру ниже отдельным сообщением
        await send_schedule_keyboard(callback.message, limit=5)

        await callback.answer()

    except Exception:
        logger.exception("on_session_click failed")
        await callback.answer("Ошибка при открытии занятия", show_alert=True)
