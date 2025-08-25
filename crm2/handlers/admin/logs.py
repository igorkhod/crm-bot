from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from crm2.utils.guards import AdminOnly
from crm2.db.core import get_db_connection
import json

router = Router()
router.callback_query.middleware(AdminOnly())

def logs_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="adm:back")],
    ])

@router.callback_query(F.data == "adm:logs")
async def logs_overview(cb: CallbackQuery):
    with get_db_connection() as con:
        last_bc = con.execute("""
            SELECT id, title, datetime(COALESCE(sent_at, 'now')), COALESCE(stats_json,'{}')
            FROM broadcasts
            ORDER BY COALESCE(sent_at, created_at) DESC
            LIMIT 5
        """).fetchall()
    if not last_bc:
        await cb.message.answer("Пока нет логов рассылок.", reply_markup=logs_menu_kb())
        await cb.answer(); return

    lines = ["Последние рассылки:"]
    for bid, title, ts, stats_json in last_bc:
        try:
            st = json.loads(stats_json)
            stat = f"sent {st.get('sent',0)}/{st.get('total',0)}, failed {st.get('failed',0)}"
        except Exception:
            stat = "(нет статистики)"
        lines.append(f"— #{bid} • {title or 'Без названия'} • {ts} • {stat}")
    await cb.message.answer("\n".join(lines), reply_markup=logs_menu_kb())
    await cb.answer()