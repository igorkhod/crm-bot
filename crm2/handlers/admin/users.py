from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from crm2.utils.guards import AdminOnly
from crm2.db.core import get_db_connection

router = Router()
router.callback_query.middleware(AdminOnly())

def users_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="adm:back")],
    ])

@router.callback_query(F.data == "adm:users")
async def users_overview(cb: CallbackQuery):
    with get_db_connection() as con:
        total = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        by_role = con.execute("SELECT COALESCE(role,'user') AS role, COUNT(*) FROM users GROUP BY COALESCE(role,'user')").fetchall()
        by_cohort = con.execute("SELECT COALESCE(c.name,'Без потока') AS cohort, COUNT(*) FROM users u LEFT JOIN cohorts c ON c.id=u.cohort_id GROUP BY cohort ORDER BY cohort").fetchall()
    roles = "\n".join(f"— {r} : {n}" for r, n in by_role)
    cohorts = "\n".join(f"— {c} : {n}" for c, n in by_cohort)
    msg = f"👥 Пользователи\nВсего: {total}\n\nПо ролям:\n{roles}\n\nПо потокам:\n{cohorts}"
    await cb.message.answer(msg, reply_markup=users_menu_kb())
    await cb.answer()