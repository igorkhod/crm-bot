#
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder


def _fmt_date(d):
    if isinstance(d, str):
        return datetime.fromisoformat(d).strftime("%d.%m.%Y")
    return d.strftime("%d.%m.%Y")


def format_range(start_date, end_date) -> str:
    return f"{_fmt_date(start_date)} — {_fmt_date(end_date)}"


def build_schedule_keyboard(sessions, show_stream: bool = False):
    """
    sessions: iterable of dicts with keys: id, start_date, end_date, topic_code, stream_id
    show_stream: если True — добавлять в подпись «· поток N»
    """
    kb = InlineKeyboardBuilder()
    for s in sessions:
        label = f"{format_range(s['start_date'], s['end_date'])} • {s.get('topic_code') or '—'}"
        if show_stream and s.get("stream_id"):
            label += f" · поток {s['stream_id']}"
        kb.button(text=label, callback_data=f"session:{s['id']}")
    kb.adjust(1)  # по одному в столбик
    return kb.as_markup()
