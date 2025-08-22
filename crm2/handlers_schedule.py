# crm2/handlers_schedule.py
from __future__ import annotations

import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.db.sessions import (
    get_upcoming_sessions,   # ожидается: sync-функция → list[dict]
    get_session_by_id,       # ожидается: sync-функция → dict | None (см. фолбэк ниже)
)

logger = logging.getLogger(__name__)

# Роутер этого модуля
schedule_router = Router(name="schedule")


def _row_text(s: dict) -> str:
    """Текст на кнопке: YYYY-MM-DD • Название темы."""
    date = s.get("start_date") or s.get("date") or ""
    title = (s.get("title") or "").strip()
    return f"{date} • {title}".strip(" •")


def _make_kb(rows: list[dict]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for s in rows:
        date = s.get("start_date") or s.get("date") or ""
        title = (s.get("title") or "").strip() or "Без темы"
        kb.button(text=f"{date} • {title}", callback_data=f"sess:{date}")
    kb.adjust(1)
    return kb


def _load_session_safe(date: str, tg_id: int | None) -> dict | None:
    """
    Универсальная загрузка карточки занятия:
    1) Пытаемся через get_session_by_id(date, tg_id)
    2) Фолбэк: ищем среди ближайших по дате.
    """
    try:
        row = get_session_by_id(date, tg_id)  # если функция принимает date — отлично
        if row:
            return row
    except Exception as e:
        logger.debug("get_session_by_id fallback: %r", e)

    try:
        rows = get_upcoming_sessions(limit=50, tg_id=tg_id) or []
    except Exception as e:
        logger.exception("get_upcoming_sessions failed in _load_session_safe")
        return None

    for r in rows:
        if (r.get("start_date") == date) or (r.get("date") == date):
            return r
    return None


async def send_schedule_keyboard(
    message: Message, *, limit: int = 5, tg_id: int | None = None
) -> None:
    """
    Рисуем блок:
      1) «Ближайшее занятие» (первая запись, если есть)
      2) «Выберите дату занятия:» + инлайн-клавиатура со всеми датами
    Никаких дублей и только корректные title.
    """
    try:
        # get_upcoming_sessions — синхронная; вызываем прямо
        sessions = get_upcoming_sessions(limit=limit, tg_id=tg_id) or []
    except Exception:
        logger.exception("send_schedule_keyboard failed")
        await message.answer("Не удалось получить расписание. Попробуйте позже.")
        return

    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    # 1) отдельным сообщением — «Ближайшее занятие»
    first = sessions[0]
    first_date = first.get("start_date") or first.get("date") or ""
    first_title = (first.get("title") or "").strip() or "Без темы"
    first_ann = (first.get("annotation") or "").strip() or "—"

    await message.answer(
        f"<b>{first_date}</b>\n\n"
        f"<b>Тема:</b> {first_title}\n"
        f"<b>Краткое описание:</b> {first_ann}"
    )

    # 2) ниже — клавиатура со всеми датами
    kb = _make_kb(sessions)
    await message.answer("Выберите дату занятия:", reply_markup=kb.as_markup())


@schedule_router.callback_query(F.data.startswith("sess:"))
async def on_session_click(callback: CallbackQuery) -> None:
    """Показываем карточку занятия по выбранной дате из callback_data=sess:YYYY-MM-DD."""
    await callback.answer()  # убрать «часики» у пользователя

    raw = callback.data or ""
    date = raw.split(":", 1)[1] if ":" in raw else ""
    tg_id = callback.from_user.id

    # грузим карточку безопасно (учёт потока по tg_id)
    row = await asyncio.to_thread(_load_session_safe, date, tg_id)

    if not row:
        await callback.message.answer("Не удалось найти занятие по этой дате.")
        return

    title = (row.get("title") or "").strip() or "Без темы"
    ann = (row.get("annotation") or "").strip() or "—"
    date_label = row.get("start_date") or row.get("date") or date

    text = (
        f"<b>{date_label}</b>\n\n"
        f"<b>Тема:</b> {title}\n"
        f"<b>Краткое описание:</b> {ann}"
    )
    await callback.message.answer(text)
