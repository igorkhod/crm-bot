# crm2/handlers/profile.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message
import sqlite3

from crm2.db.sqlite import DB_PATH
from crm2.keyboards.profile import profile_menu_kb
from crm2.keyboards import role_kb, guest_start_kb
from crm2.db.sessions import get_upcoming_sessions, get_user_cohort_title_by_tg
from crm2.db.attendance import get_last_attendance, get_summary

router = Router(name="profile")

def _get_user_row(tg_id: int):
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        return con.execute(
            "SELECT id, full_name, nickname, role FROM users WHERE telegram_id=? LIMIT 1",
            (tg_id,),
        ).fetchone()

@router.message(F.text == "👤 Личный кабинет")
async def show_profile(message: Message):
    tg_id = message.from_user.id
    row = _get_user_row(tg_id)

    if not row:
        # гость
        await message.answer(
            "Вы пока гость. Войдите или зарегистрируйтесь, чтобы открыть личный кабинет.",
            reply_markup=guest_start_kb(),
        )
        return

    uid = row["id"]
    role = row["role"] or "user"
    fio = row["full_name"] or message.from_user.full_name or (row["nickname"] or "")
    cohort_id, cohort_title = get_user_cohort_title_by_tg(tg_id)

    # ближайшее занятие для конкретного пользователя (с его потоком, если он есть)
    nearest = None
    upc = get_upcoming_sessions(limit=1, tg_id=tg_id)
    if upc:
        s = upc[0]
        d1, d2 = s["start_date"], s["end_date"]
        code = (s.get("topic_code") or "").strip()
        dates = f"{d1} — {d2}" if (d1 and d2 and d1 != d2) else (d1 or d2 or "—")
        nearest = f"{dates}" + (f" • {code}" if code else "")

    # посещаемость: суммарно и последние 3 записи
    present, absent, late = get_summary(uid)
    last3 = get_last_attendance(uid, limit=3)
    if last3:
        last_lines = "\n".join([f"• #{sid}: {st} ({at})" for (sid, st, at) in last3])
    else:
        last_lines = "• записей пока нет"

    text = (
        "👤 *Личный кабинет*\n\n"
        f"*ФИО:* {fio}\n"
        f"*Роль:* {role}\n"
        f"*Поток:* {cohort_title or 'Без потока'}\n"
        f"*Ближайшее занятие:* {nearest or '—'}\n\n"
        f"*Посещаемость:*\n"
        f"Был: {present} · Пропустил: {absent} · Опоздал: {late}\n"
        f"_Последние записи:_\n{last_lines}\n\n"
        "Раздел «Мои материалы» — скоро."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=profile_menu_kb())

@router.message(F.text == "🔔 Уведомления: вкл/выкл")
async def toggle_notify(message: Message):
    # переключатель user_flags.notify_enabled
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        u = con.execute("SELECT id FROM users WHERE telegram_id=? LIMIT 1", (message.from_user.id,)).fetchone()
        if not u:
            await message.answer("Для переключения уведомлений войдите в систему.", reply_markup=guest_start_kb())
            return
        uid = u["id"]
        # текущее значение
        r = con.execute("SELECT notify_enabled FROM user_flags WHERE user_id=? LIMIT 1", (uid,)).fetchone()
        cur = (r["notify_enabled"] if r else 1)
        nxt = 0 if cur else 1
        if r:
            con.execute("UPDATE user_flags SET notify_enabled=? WHERE user_id=?", (nxt, uid))
        else:
            con.execute("INSERT INTO user_flags(user_id, notify_enabled) VALUES (?, ?)", (uid, nxt))
        con.commit()

    await message.answer(f"Уведомления: {'включены' if nxt else 'выключены'}")

@router.message(F.text == "📄 Мои материалы")
async def my_materials(message: Message):
    # пока заглушка
    await message.answer("Мои материалы: скоро здесь появится список новых PDF/ссылок.")
