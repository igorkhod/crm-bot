from __future__ import annotations

import os
import sqlite3
import logging
from datetime import date, datetime
from typing import Optional, Iterable

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from crm2.db.core import get_db_connection
from crm2.handlers.admin.panel import open_admin_menu
from crm2.keyboards.admin_attendance import (
    attendance_root_kb,
    attendance_users_kb,
)
# crm2/handlers/admin_attendance.py
log = logging.getLogger(__name__)
router = Router()

# --- access ---------------------------------------------------------

ADMIN_ID = os.getenv("ADMIN_ID")
try:
    ADMIN_ID_INT = int(ADMIN_ID) if ADMIN_ID else None
except Exception:
    ADMIN_ID_INT = None


def _is_admin(ev: Message | CallbackQuery) -> bool:
    uid = ev.from_user.id if hasattr(ev, "from_user") else None
    ok = ADMIN_ID_INT is not None and uid == ADMIN_ID_INT
    if not ok:
        log.debug("[ACCESS] denied: uid=%s ADMIN_ID=%s", uid, ADMIN_ID_INT)
    return ok


# --- helpers --------------------------------------------------------

def _fmt_d(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def _rowdicts(cur) -> list[dict]:
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# --- DB: session_days / users / attendance -------------------------

def _today_session_day() -> Optional[dict]:
    today_iso = date.today().strftime("%Y-%m-%d")
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT id, date, stream_id, COALESCE(topic_code,'') AS topic_code "
            "FROM session_days WHERE date = ? LIMIT 1",
            (today_iso,),
        ).fetchone()
        log.debug("[DB] today_session_day -> %s", dict(row) if row else None)
        return dict(row) if row else None


def _recent_past_session_days(limit: int = 2) -> list[dict]:
    today_iso = date.today().strftime("%Y-%m-%d")
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            "SELECT id, date, stream_id, COALESCE(topic_code,'') AS topic_code "
            "FROM session_days "
            "WHERE date < ? "
            "ORDER BY date DESC LIMIT ?",
            (today_iso, limit),
        )
        data = _rowdicts(cur)
        log.debug("[DB] recent_past_session_days(%s) -> %s", limit, data)
        return data


def _session_day_by_id(sd_id: int) -> Optional[dict]:
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT id, date, stream_id, COALESCE(topic_code,'') AS topic_code "
            "FROM session_days WHERE id = ?",
            (sd_id,),
        ).fetchone()
        log.debug("[DB] session_day_by_id(%s) -> %s", sd_id, dict(row) if row else None)
        return dict(row) if row else None


def _users_of_stream(stream_id: int) -> list[dict]:
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            """
            SELECT u.id, u.full_name, u.username, u.nickname, u.telegram_id
            FROM participants p
            JOIN users u ON u.id = p.user_id
            WHERE p.stream_id = ?
            ORDER BY u.full_name COLLATE NOCASE, u.id
            """,
            (stream_id,),
        )
        data = _rowdicts(cur)
        log.debug("[DB] users_of_stream(%s) -> %d users", stream_id, len(data))
        return data


def _attendance_map(session_id: int) -> dict[int, str]:
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            "SELECT user_id, status FROM attendance WHERE session_id = ?",
            (session_id,),
        )
        data = {int(r["user_id"]): str(r["status"]) for r in cur.fetchall()}
        log.debug("[DB] attendance_map(session_id=%s) -> %s", session_id, data)
        return data


def _upsert_attendance(user_id: int, session_id: int, status: str, noted_by: int) -> None:
    log.debug("[DB] upsert_attendance u=%s s=%s status=%s by=%s",
              user_id, session_id, status, noted_by)
    with get_db_connection() as con:
        con.execute(
            """
            INSERT INTO attendance(user_id, session_id, status, noted_by)
            VALUES (?,?,?,?)
            ON CONFLICT(user_id, session_id) DO UPDATE SET
              status   = excluded.status,
              noted_at = CURRENT_TIMESTAMP,
              noted_by = excluded.noted_by
            """,
            (user_id, session_id, status, noted_by),
        )
        con.commit()


# --- entry ----------------------------------------------------------
# принимаем И старое, и новое callback_data
@router.callback_query(F.data.in_({"admin:attendance", "admin:att:root"}))
async def admin_attendance_entry(cq: CallbackQuery):
    log.debug("[ENTRY] admin_attendance_entry data=%s", cq.data)
    if not _is_admin(cq):
        return await cq.answer("Доступ только для администратора", show_alert=True)

    today = date.today()
    sd = _today_session_day()

    if sd:
        # Вариант 2: сегодня занятие
        text = (
            f"Сегодня {_fmt_d(today)}.\n"
            f"Занятие потока {sd['stream_id']}, {sd.get('topic_code') or 'сессия'}.\n\n"
            f"Нажмите «Регистрация» для отметки присутствия."
        )
        kb = attendance_root_kb(today_session=sd, past=[])
        await cq.message.answer(text, reply_markup=kb.as_markup(), parse_mode=None)
        return await cq.answer("Открыта регистрация на сегодня")

    # Вариант 1: занятий сегодня нет
    past = _recent_past_session_days(limit=2)
    pretty = " • ".join(
        f"поток {r['stream_id']} — {r.get('topic_code') or 'сессия'} — "
        f"{_fmt_d(datetime.fromisoformat(r['date']).date())}"
        for r in past
    ) or "варианты отсутствуют"
    text = (
        f"Сегодня {_fmt_d(today)}, занятий нет.\n\n"
        f"Какому потоку и на какую дату будете отмечать посещение?\n\n"
        f"Ближайшие прошедшие: {pretty}"
    )
    kb = attendance_root_kb(today_session=None, past=past)
    await cq.message.answer(text, reply_markup=kb.as_markup(), parse_mode=None)
    await cq.answer("Выберите дату")


# --- open session ----------------------------------------------------

@router.callback_query(F.data.startswith("admin:att:open:"))
async def admin_attendance_open(cq: CallbackQuery):
    if not _is_admin(cq):
        return await cq.answer("Нет прав", show_alert=True)
    sd_id = int(cq.data.split(":")[-1])
    log.debug("[OPEN] session_day id=%s", sd_id)

    sd = _session_day_by_id(sd_id)
    if not sd:
        log.warning("[OPEN] session_day not found: %s", sd_id)
        return await cq.answer("Сессия не найдена", show_alert=True)

    d = datetime.fromisoformat(sd["date"]).date()
    users = _users_of_stream(int(sd["stream_id"]))
    marks = _attendance_map(sd_id)

    header = (
        f"Отметка посещаемости\n"
        f"Поток {sd['stream_id']} • {sd.get('topic_code') or 'сессия'} • {_fmt_d(d)}\n\n"
        f"Нажимайте на имена для переключения статуса:\n"
        f"⬜️ → ✅ присутствовал → ❌ отсутствовал → ⛔️ (>2 пропусков) → ⬜️"
    )
    kb = attendance_users_kb(sd_id, users, marks)
    await cq.message.answer(header, reply_markup=kb.as_markup(), parse_mode=None)
    await cq.answer("Открыт список слушателей")


# --- toggle ----------------------------------------------------------

@router.callback_query(F.data.startswith("admin:att:toggle:"))
async def admin_attendance_toggle(cq: CallbackQuery):
    if not _is_admin(cq):
        return await cq.answer("Нет прав", show_alert=True)

    _, _, _, sess_id_str, user_id_str = cq.data.split(":")
    session_id = int(sess_id_str)
    user_id = int(user_id_str)
    log.debug("[TOGGLE] session_id=%s user_id=%s", session_id, user_id)

    marks = _attendance_map(session_id)
    curr = marks.get(user_id)  # None|'present'|'absent'|'expelled'
    nxt = (
        "present" if curr is None else
        "absent" if curr == "present" else
        "expelled" if curr == "absent" else
        None
    )
    log.debug("[TOGGLE] current=%s next=%s", curr, nxt)

    if nxt is None:
        with get_db_connection() as con:
            con.execute("DELETE FROM attendance WHERE user_id = ? AND session_id = ?",
                        (user_id, session_id))
            con.commit()
        msg = "Отметка сброшена"
    else:
        _upsert_attendance(user_id, session_id, nxt, noted_by=cq.from_user.id)
        msg = {"present": "✅ присутствовал", "absent": "❌ отсутствовал",
               "expelled": "⛔️ отчислен"}[nxt]

    sd = _session_day_by_id(session_id)
    users = _users_of_stream(int(sd["stream_id"])) if sd else []
    new_marks = _attendance_map(session_id)
    await cq.message.edit_reply_markup(
        reply_markup=attendance_users_kb(session_id, users, new_marks).as_markup()
    )
    await cq.answer(msg)


# --- back ------------------------------------------------------------

@router.callback_query(F.data == "admin:back")
async def admin_back(cq: CallbackQuery):
    await cq.answer()
    await open_admin_menu(cq.message)
