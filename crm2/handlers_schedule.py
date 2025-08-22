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
    """
    Рисуем блок:
      - «Ближайшее занятие:» (первая запись, если есть)
      - «Выберите дату занятия:» (кнопки по всем записям)
    Никаких дублей. Заголовок = именно s['title'].
    """
    try:
        sessions = sessions_db.get_upcoming_sessions(limit=limit, tg_id=tg_id)  # sync → внутри DB
    except Exception as e:
        logger.exception("send_schedule_keyboard failed")
        await message.answer("Не удалось получить расписание. Попробуйте позже.")
        return

    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return

    # 1) отдельным сообщением — «Ближайшее занятие»
    first = sessions[0]
    await message.answer(
        f"<b>{first['start_date']}</b>\n<b>Тема:</b> {first.get('title','').strip()}",
        parse_mode="HTML",
    )

    # 2) ниже — клавиатура со всеми датами
    kb = InlineKeyboardBuilder()
    for s in sessions:
        text = f"{s['start_date']} • {s.get('title','').strip() or 'Без темы'}"
        kb.button(text=text, callback_data=f"sess:{s['start_date']}")

    kb.adjust(1)
    await message.answer("Выберите дату занятия:", reply_markup=kb.as_markup())
