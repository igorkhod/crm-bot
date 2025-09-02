# === Автогенерированный заголовок: crm2/keyboards/schedule.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: _fmt_date, format_range, build_schedule_keyboard
# === Конец автозаголовка
#
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder


def schedule_root_kb() -> "InlineKeyboardMarkup":
    kb = InlineKeyboardBuilder()
    kb.button(text="1 поток", callback_data="sch:cohort:1")
    kb.button(text="2 поток", callback_data="sch:cohort:2")
    kb.button(text="Мероприятия", callback_data="sch:events")
    kb.button(text="Все события", callback_data="sch:all")
    kb.adjust(2, 2)
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
