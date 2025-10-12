# crm2/keyboards/schedule.py
# Назначение: Клавиатуры и утилиты для работы с расписанием (inline-навигация)
# Функции:
# - _fmt_date - Форматирование даты в единый формат
# - format_range - Форматирование диапазона дат
# - build_schedule_keyboard - Построение клавиатуры списка сессий
# - schedule_root_kb - Главное меню расписания (потоки, мероприятия, все события)
# - schedule_dates_kb - Клавиатура дат сессий для конкретной когорты
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def schedule_root_kb() -> "InlineKeyboardMarkup":
    kb = InlineKeyboardBuilder()
    kb.button(text="1 поток", callback_data="sch:cohort:1")
    kb.button(text="2 поток", callback_data="sch:cohort:2")
    kb.button(text="Мероприятия", callback_data="sch:events")
    kb.button(text="Все события", callback_data="sch:all")
    kb.adjust(2, 2)
    return kb.as_markup()


def schedule_dates_kb(cohort_id: int, sessions) -> InlineKeyboardMarkup:
    """Макс. 5 кнопок: каждая — дата/диапазон, callback с датой начала."""
    kb = InlineKeyboardBuilder()
    for s in (sessions or [])[:5]:
        left = s.start.strftime("%d.%m.%Y")
        right = s.end.strftime("%d.%m.%Y") if s.end != s.start else None
        label = f"{left} — {right} · {s.code or s.title}" if right else f"{left} · {s.code or s.title}"
        kb.button(text=label, callback_data=f"sch:cohort:{cohort_id}:{s.start.isoformat()}")
    kb.adjust(1)
    return kb.as_markup()

def _fmt_date(d):
    if isinstance(d, str):
        return datetime.fromisoformat(d).strftime("%d.%m.%Y")
    return d.strftime("%d.%m.%Y")


def format_range(start_date, end_date) -> str:
    return f"{_fmt_date(start_date)} — {_fmt_date(end_date)}"


def build_schedule_keyboard(sessions, show_cohort: bool = False):
    """
    sessions: iterable of dicts with keys: id, start_date, end_date, topic_code, cohort_id
    show_cohort: если True — добавлять в подпись «· поток N»
    """
    kb = InlineKeyboardBuilder()
    for s in sessions:
        label = f"{format_range(s['start_date'], s['end_date'])} • {s.get('topic_code') or '—'}"
        if show_cohort and s.get("cohort_id"):
            label += f" · поток {s['cohort_id']}"
        kb.button(text=label, callback_data=f"session:{s['id']}")
    kb.adjust(1)  # по одному в столбик
    return kb.as_markup()
