from __future__ import annotations

import logging, re  # ← ДОБАВЬ
import sqlite3
from html import escape
from typing import Optional

from aiogram import Router, F  # ← БЫЛО: from aiogram import Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from crm2.db.sessions import get_upcoming_sessions, get_session_by_id
from crm2.keyboards import format_range

logger = logging.getLogger(__name__)

schedule_router = Router()


def _detect_table_name(cur: sqlite3.Cursor) -> Optional[str]:
    cur.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                  AND name IN
                      ('events_xlsx', 'events_ui', 'v_upcoming_days', 'session_index', 'sessions', 'schedule', 'events')
                ORDER BY CASE name
                             WHEN 'events_xlsx' THEN 1
                             WHEN 'events_ui' THEN 2
                             WHEN 'v_upcoming_days' THEN 3
                             WHEN 'session_index' THEN 4
                             WHEN 'sessions' THEN 5
                             WHEN 'schedule' THEN 6
                             WHEN 'events' THEN 7
                             ELSE 99 END LIMIT 1
                """)
    r = cur.fetchone()
    return r["name"] if r else None


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


def _row_text(s: dict) -> str:
    return f"{s['start_date']} — {s['end_date']} • {s.get('topic_code') or ''}".strip()


async def send_schedule_keyboard(message: Message, limit: int = 5, tg_id: int | None = None):
    sessions = await get_upcoming_sessions(limit=limit, tg_id=tg_id)
    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    # 1) Отдельно — ближайшее
    first = sessions[0]
    nearest_kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=_row_text(first),
                callback_data=f"session:{first['id']}"
            )
        ]]
    )
    await message.answer("Ближайшее занятие:", reply_markup=nearest_kb)

    # 2) Остальные (без дублирования первой)
    tail = sessions[1:]
    if not tail:
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_row_text(s), callback_data=f"session:{s['id']}")]
            for s in tail
        ]
    )
    await message.answer("Выберите дату занятия:", reply_markup=kb)


@schedule_router.callback_query(F.data.startswith("session:"))
async def on_session_click(callback: CallbackQuery):
    sid = int(callback.data.split(":", 1)[1])
    s = await get_session_by_id(sid)
    if not s:
        await callback.answer("Не удалось найти занятие", show_alert=True)
        return

    header = f"{s['start_date']} — {s['end_date']} • {s.get('topic_code') or ''}".strip()
    title = s.get("title") or "—"
    annotation = s.get("annotation") or "—"
    text = (
        f"<b>{header}</b>\n\n"
        f"<b>Тема:</b> {title}\n"
        f"<b>Краткое описание:</b> {annotation}"
    )
    await callback.message.answer(text)
    await callback.answer()


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


#

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
