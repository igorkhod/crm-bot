# crm2/keyboards/session_picker.py
# Назначение: Специализированная клавиатура для выбора сессий с датами и кодами
# Функции:
# - build_session_picker - Построение клавиатуры выбора сессии с группировкой по режиму
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_session_picker(sessions, mode: str) -> InlineKeyboardMarkup:
    rows = []
    for s in sessions:
        d1, d2 = s["start_date"], s.get("end_date")
        dates = f"{d1} — {d2}" if d2 and d2 != d1 else (d1 or d2 or "—")
        code = (s.get("topic_code") or "—").strip()
        text = f"{dates} • {code}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"pick_session:{mode}:{s['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
