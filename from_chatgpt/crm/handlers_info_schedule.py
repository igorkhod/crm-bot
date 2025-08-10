from aiogram import Router, types, F
from aiogram.filters import Command
import aiosqlite
from datetime import datetime
from from_chatgpt.crm.db import DB_PATH

# Роутер раздела «Информация»
info_schedule_router = Router()

def _weekday_ru(dt: datetime) -> str:
    days = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
    return days[dt.weekday()]

@info_schedule_router.message(Command("расписание"))
async def cmd_schedule(message: types.Message):
    """/расписание — ближайшие 10 «дней занятий» из session_days."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            """
            SELECT cohort_id, seq, course_kind, title, date
            FROM session_days
            WHERE date >= DATE('now')
            ORDER BY date
            LIMIT 10
            """
        )).fetchall()
        cohorts = await (await db.execute(
            """
            SELECT DISTINCT cohort_id
            FROM session_days
            WHERE date >= DATE('now')
            ORDER BY cohort_id
            """
        )).fetchall()

    if not rows:
        await message.answer("📭 Расписание пока пусто.")
        return

    lines = ["📅 <b>Ближайшие занятия</b>:"]
    for r in rows:
        d = datetime.fromisoformat(r["date"])
        lines.append(f"{d.strftime('%d.%m.%Y')} ({_weekday_ru(d)}) — {r['course_kind']} {r['seq']}: {r['title']}  [{r['cohort_id']}]")

    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text=c[0], callback_data=f"info_sched_cohort:{c[0]}")
    ] for c in cohorts])
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=kb)

@info_schedule_router.callback_query(F.data.startswith("info_sched_cohort:"))
async def cb_schedule_by_cohort(callback: types.CallbackQuery):
    cohort_id = callback.data.split(":", 1)[1]
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            """
            SELECT cohort_id, seq, course_kind, title, date
            FROM session_days
            WHERE date >= DATE('now') AND cohort_id = ?
            ORDER BY date
            LIMIT 20
            """, (cohort_id,)
        )).fetchall()
    if not rows:
        await callback.message.edit_text(f"Для потока [{cohort_id}] ближайших занятий не найдено.")
        await callback.answer()
        return

    lines = [f"📅 <b>Ближайшие занятия — {cohort_id}</b>:"]
    for r in rows:
        d = datetime.fromisoformat(r["date"])
        lines.append(f"{d.strftime('%d.%m.%Y')} ({_weekday_ru(d)}) — {r['course_kind']} {r['seq']}: {r['title']}")
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML")
    await callback.answer()
