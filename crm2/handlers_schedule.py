from __future__ import annotations

import logging
import re                    # ← ДОБАВЬ
from html import escape

from aiogram import Router, F  # ← БЫЛО: from aiogram import Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from crm2.db import get_upcoming_sessions, get_session_by_id
from crm2.keyboards import build_schedule_keyboard, format_range

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
async def send_schedule_keyboard(message: Message, *, limit: int = 5, include_nearest: bool = True, tg_id: int | None = None) -> None:

    sessions = await get_upcoming_sessions(limit=limit, tg_id=tg_id)

    try:
        sessions = await get_upcoming_sessions(limit=limit)
    except Exception:
        logger.exception("send_schedule_keyboard failed")
        await message.answer("Расписание временно недоступно. Попробуйте позже.")
        return

    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    if include_nearest:
        first = sessions[0]
        first_text = f"{format_range(first['start_date'], first['end_date'])} • {first.get('topic_code') or '—'}"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=first_text, callback_data=f"nearest:{first['id']}")]]
        )
        await message.answer("Ближайшее занятие:", reply_markup=kb)
        rest = sessions[1:]
    else:
        rest = sessions

    if rest:
        await message.answer(
            "Выберите дату занятия:",
            reply_markup=build_schedule_keyboard(rest),
        )


async def _render_session_card(callback: CallbackQuery, s: dict, *, show_rest: bool) -> None:
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

    # превращаем сообщение-кнопку в карточку и убираем инлайн-клавиатуру
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=None)

    # если это клик по кнопке из списка дат — обновим список ниже (без "ближайшего")
    if show_rest:
        await send_schedule_keyboard(callback.message, limit=5, include_nearest=False, tg_id=callback.from_user.id)

    await callback.answer()


# @schedule_router.callback_query(lambda c: c.data and c.data.startswith("nearest:"))
@schedule_router.callback_query(F.data.startswith("nearest:"))
async def on_nearest_click(callback: CallbackQuery) -> None:
    try:
        session_id = int(callback.data.split(":", 1)[1])
        s = await get_session_by_id(session_id)
        if not s:
            await callback.answer("Занятие не найдено", show_alert=True)
            return
        await _render_session_card(callback, s, show_rest=False)
    except Exception:
        logger.exception("on_nearest_click failed")
        await callback.answer("Ошибка при открытии занятия", show_alert=True)


# Ловим любые привычные префиксы + ID в конце: session:42 / day:42 / schedule:42 / event:42 / s:42
@schedule_router.callback_query(F.data.regexp(r"^(?:session|day|schedule|event|s):\d+$"))
async def on_session_click_generic(callback: CallbackQuery) -> None:
    try:
        m = re.search(r"(\d+)$", callback.data or "")
        if not m:
            return
        session_id = int(m.group(1))
        s = await get_session_by_id(session_id)
        if not s:
            return
        await _render_session_card(callback, s, show_rest=True)
    except Exception:
        logger.exception("on_session_click_generic failed")
        await callback.answer("Ошибка при открытии занятия", show_alert=True)


@schedule_router.callback_query()
async def on_unknown_callback(callback: CallbackQuery) -> None:
    # Если это не наше — просто ответим ничем и дадим шанс другим роутерам
    logger.warning("Unknown callback (schedule router): %r", callback.data)
    await callback.answer()

