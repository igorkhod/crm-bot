from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from crm2.utils.guards import AdminOnly
from crm2.db.core import get_db_connection
from crm2.db.schedule_loader import sync_schedule_from_files

router = Router()
router.callback_query.middleware(AdminOnly())

def schedule_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Импорт из XLSX", callback_data="adm:schedule:import")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="adm:back")],
    ])

@router.callback_query(F.data == "adm:schedule")
async def schedule_entry(cb: CallbackQuery):
    with get_db_connection() as con:
        rows = con.execute("""
            SELECT date, topic_code, (SELECT title FROM topics t WHERE t.id=sd.topic_id) AS title
            FROM session_days sd
            WHERE date >= date('now')
            ORDER BY date
            LIMIT 5
        """).fetchall()
    if not rows:
        text = "Ближайших занятий пока не видно."
    else:
        text = "Ближайшие занятия:\n" + "\n".join(f"— {r[0]} • {r[1]} • {r[2] or ''}" for r in rows)
    await cb.message.answer(text, reply_markup=schedule_menu_kb())
    await cb.answer()

@router.callback_query(F.data == "adm:schedule:import")
async def schedule_import(cb: CallbackQuery):
    try:
        affected = sync_schedule_from_files([
            "schedule_2025_1_cohort.xlsx",
            "schedule_2025_2_cohort.xlsx",
            "crm2/data/schedule 2025 1 cohort.xlsx",
            "crm2/data/schedule 2025 2 cohort.xlsx",
        ])
        if affected is None:
            msg = "Импорт выполнен."
        else:
            msg = f"Импорт выполнен, обновлено строк: {affected}."
    except Exception as e:
        msg = f"Ошибка импорта: {e}"
    await cb.message.answer(msg, reply_markup=schedule_menu_kb())
    await cb.answer()