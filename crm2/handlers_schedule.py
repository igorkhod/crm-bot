
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

from crm2.db.sessions import (
    get_upcoming_sessions,
    get_session_by_id,
    get_upcoming_sessions_by_stream,  # ← потребуется функция в sessions.py
)

from crm2.keyboards.schedule import build_schedule_keyboard, format_range

logger = logging.getLogger(__name__)
router = Router(name="schedule")

async def send_schedule_keyboard(
    message: Message,
    *,
    limit: int = 5,
    tg_id: int | None = None,
    stream_id: int | None = None
) -> None:
    """
    Renders:
      1) "Ближайшее занятие: DD.MM.YYYY — DD.MM.YYYY • CODE"
      2) Inline keyboard with all available upcoming dates (date range + code).
    """
    try:
        if stream_id is not None:
            sessions = get_upcoming_sessions_by_stream(stream_id=stream_id, limit=limit) or []
        else:
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
        "Выберите дату занятия для получения более детальной информации:",
        reply_markup=build_schedule_keyboard(sessions),
    )

async def send_nearest_session(message: Message, *, tg_id: int | None = None, limit: int = 5) -> None:
    """
    Шлёт ТОЛЬКО одну строку «Ближайшее занятие: …», без клавиатуры.
    """
    try:
        sessions = get_upcoming_sessions(limit=limit, tg_id=tg_id) or []
    except Exception:
        logger.exception("send_nearest_session failed")
        await message.answer("Ближайших занятий пока нет.")
        return
    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return
    first = sessions[0]
    code = (first.get("topic_code") or "").strip()
    line = f"Ближайшее занятие: {format_range(first['start_date'], first['end_date'])}"
    if code:
        line += f" • {code}"
    await message.answer(line)

def _info_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="1 поток · набор 09.2023")],
        [KeyboardButton(text="2 поток · набор 09.2023")],
        [KeyboardButton(text="Новый набор · 2025")],
        # Кнопку «Мероприятия» добавим после подключения db/events.py
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

async def show_info_menu(message: Message) -> None:
    await message.answer("Выберите раздел:", reply_markup=_info_menu_kb())

# --- Обработчики пунктов меню выбора потока ---
@router.message(F.text == "1 поток · набор 09.2023")
async def _show_stream1(message: Message):
    await send_schedule_keyboard(message, limit=5, tg_id=message.from_user.id, stream_id=1)

@router.message(F.text == "2 поток · набор 09.2023")
async def _show_stream2(message: Message):
    await send_schedule_keyboard(message, limit=5, tg_id=message.from_user.id, stream_id=2)

@router.message(F.text == "Новый набор · 2025")
async def _show_new(message: Message):
    await message.answer("Начало занятий по мере комплектования группы.")


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
__all__ = ['schedule_router', 'router', 'send_schedule_keyboard', 'send_nearest_session', 'show_info_menu']
