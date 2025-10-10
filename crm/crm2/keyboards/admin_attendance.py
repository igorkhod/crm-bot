
from __future__ import annotations

from datetime import datetime
from aiogram.utils.keyboard import InlineKeyboardBuilder


def _fmt(date_iso: str) -> str:
    d = datetime.fromisoformat(date_iso).date()
    return d.strftime("%d.%m.%Y")


def attendance_root_kb(today_session: dict | None, past: list[dict]) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if today_session:
        kb.button(text="📝 Регистрация (сегодня)", callback_data=f"admin:att:open:{today_session['id']}")
    for r in past:
        title = f"Поток {r['stream_id']} • {r.get('topic_code') or 'сессия'} • {_fmt(r['date'])}"
        kb.button(text=title, callback_data=f"admin:att:open:{r['id']}")
    kb.button(text="⬅️ В админ-панель", callback_data="admin:back")
    kb.adjust(1)
    return kb


# ========== ПАТЧ 4: Обновление иконок статусов ==========
# ДО (строки 22-30):
# def attendance_users_kb(session_id: int, users: list[dict], marks: dict[int, str]) -> InlineKeyboardBuilder:
#     def icon(u_id: int) -> str:
#         st = marks.get(u_id)
#         return "✅" if st == "present" else "❌" if st == "absent" else "⛔️" if st == "expelled" else "⬜️"

# ПОСЛЕ:
def attendance_users_kb(session_id: int, users: list[dict], marks: dict[int, str]) -> InlineKeyboardBuilder:
    def icon(u_id: int) -> str:
        st = marks.get(u_id)
        # ✅ ИСПРАВЛЕНО: late вместо expelled
        return (
            "✅" if st == "present" else
            "❌" if st == "absent" else
            "⏰" if st == "late" else
            "⬜️"
        )
# ========== КОНЕЦ ПАТЧА 4 ==========

    kb = InlineKeyboardBuilder()
    for u in users:
        u_id = int(u["id"])
        name = u.get("full_name") or u.get("nickname") or u.get("username") or f"user#{u_id}"
        kb.button(text=f"{icon(u_id)} {name}", callback_data=f"admin:att:toggle:{session_id}:{u_id}")
    kb.button(text="⬅️ Назад к датам", callback_data="admin:att:root")
    kb.button(text="⬅️ В админ-панель", callback_data="admin:back")
    kb.adjust(1)
    return kb


# ====================================================================================================================
# crm2/keyboards/admin_attendance.py

# from __future__ import annotations
#
# from datetime import datetime
# from aiogram.utils.keyboard import InlineKeyboardBuilder
#
#
# def _fmt(date_iso: str) -> str:
#     d = datetime.fromisoformat(date_iso).date()
#     return d.strftime("%d.%m.%Y")
#
#
# def attendance_root_kb(today_session: dict | None, past: list[dict]) -> InlineKeyboardBuilder:
#     kb = InlineKeyboardBuilder()
#     if today_session:
#         kb.button(text="📝 Регистрация (сегодня)", callback_data=f"admin:att:open:{today_session['id']}")
#     for r in past:
#         title = f"Поток {r['stream_id']} • {r.get('topic_code') or 'сессия'} • {_fmt(r['date'])}"
#         kb.button(text=title, callback_data=f"admin:att:open:{r['id']}")
#     kb.button(text="⬅️ В админ-панель", callback_data="admin:back")
#     kb.adjust(1)
#     return kb
#
#
# def attendance_users_kb(session_id: int, users: list[dict], marks: dict[int, str]) -> InlineKeyboardBuilder:
#     def icon(u_id: int) -> str:
#         st = marks.get(u_id)
#         return "✅" if st == "present" else "❌" if st == "absent" else "⛔️" if st == "expelled" else "⬜️"
#
#     kb = InlineKeyboardBuilder()
#     for u in users:
#         u_id = int(u["id"])
#         name = u.get("full_name") or u.get("nickname") or u.get("username") or f"user#{u_id}"
#         kb.button(text=f"{icon(u_id)} {name}", callback_data=f"admin:att:toggle:{session_id}:{u_id}")
#     kb.button(text="⬅️ Назад к датам", callback_data="admin:att:root")
#     kb.button(text="⬅️ В админ-панель", callback_data="admin:back")
#     kb.adjust(1)
#     return kb
# crm2/keyboards/admin_attendance.py