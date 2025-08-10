import os
from datetime import datetime

import aiosqlite
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from from_chatgpt.crm.db import DB_PATH
from crm.db import get_user_by_nickname

router = Router()

# ------------------ Вспомогательные ------------------
def _weekday_ru(dt: datetime) -> str:
    days = {
        0: "Понедельник", 1: "Вторник", 2: "Среда",
        3: "Четверг",     4: "Пятница", 5: "Суббота", 6: "Воскресенье"
    }
    return days[dt.weekday()]


def _is_admin(message: Message, state_data: dict) -> bool:
    """
    Надёжное определение администратора:
    - если в FSM записана роль 'admin'
    - либо если from_user.id совпадает с ADMIN_ID из окружения
    (читаем ADMIN_ID напрямую из os.environ в момент вызова, а не на этапе импорта)
    """
    role = state_data.get("role")
    admin_env = os.getenv("ADMIN_ID")
    return (role == "admin") or (admin_env and str(message.from_user.id) == str(admin_env))


async def _user_cohorts(db, user_id: int, nickname: str):
    """Возвращает список cohort_id, к которым привязан пользователь (по user_id, затем по nickname)."""
    # по user_id
    try:
        rows = await (await db.execute(
            "SELECT DISTINCT cohort_id FROM participants WHERE user_id = ?", (user_id,)
        )).fetchall()
        if rows:
            return [r[0] for r in rows]
    except Exception:
        pass
    # по nickname
    try:
        rows = await (await db.execute(
            "SELECT DISTINCT cohort_id FROM participants WHERE nickname = ?", (nickname,)
        )).fetchall()
        if rows:
            return [r[0] for r in rows]
    except Exception:
        pass
    return []


async def _next_session_for_cohorts(db, cohort_ids):
    """Ближайший день занятия среди потоков + title/notes из course_sessions."""
    if not cohort_ids:
        return None
    placeholders = ",".join("?" * len(cohort_ids))
    day_row = await (await db.execute(
        f"""
        SELECT session_id, cohort_id, date
        FROM session_days
        WHERE cohort_id IN ({placeholders}) AND date >= DATE('now')
        ORDER BY date
        LIMIT 1
        """,
        cohort_ids
    )).fetchone()
    if not day_row:
        return None
    sess = await (await db.execute(
        "SELECT title, notes FROM course_sessions WHERE id = ?", (day_row["session_id"],)
    )).fetchone()
    return {
        "cohort_id": day_row["cohort_id"],
        "date": day_row["date"],
        "title": (sess["title"] if sess else ""),
        "notes": (sess["notes"] if (sess and sess["notes"]) else ""),
    }


# ------------------ Коллбэки/кнопки раздела Информация ------------------
@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: CallbackQuery):
    await callback.message.answer("🔧 Здесь будет управление пользователями (удаление, блокировка, назначение ролей).")


@router.callback_query(F.data == "info")
async def info_callback_proxy(callback: CallbackQuery, state: FSMContext):
    # Переиспользуем обработчик кнопки «Информация» (reply-кнопка)
    await info_button_handler(callback.message, state)


@router.message(F.text == "Информация")
async def info_button_handler(message: Message, state: FSMContext):
    """Админ — общий календарь. Участник — ближайшее занятие (дата, тема, содержание)."""
    data = await state.get_data()
    user_id  = data.get("user_id") or 0
    nickname = data.get("nickname") or ""

    # fallback: если ник в FSM пуст, попробуем взять из username телеграма
    if not nickname and message.from_user and message.from_user.username:
        nickname = message.from_user.username

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if _is_admin(message, data):
            rows = await (await db.execute(
                """
                SELECT cohort_id, title, date
                FROM session_days
                WHERE date >= DATE('now')
                ORDER BY date
                LIMIT 50
                """
            )).fetchall()
            if not rows:
                await message.answer("Ближайших занятий (по всем потокам) не найдено.")
                return
            lines = ["📅 <b>Ближайшие занятия (все потоки)</b>:"]
            for r in rows:
                d = datetime.fromisoformat(r["date"])
                lines.append(f"{d.strftime('%d.%m.%Y')} ({_weekday_ru(d)}) — {r['title']}  [{r['cohort_id']}]")
            await message.answer("\n".join(lines), parse_mode="HTML")
            return

        # Участник: ищем его потоки
        if not user_id and nickname:
            db_user = await get_user_by_nickname(nickname)
            if db_user:
                user_id = db_user.get("id", 0)

        cohorts = await _user_cohorts(db, user_id, nickname)
        if not cohorts:
            await message.answer("Для вашего профиля не найден привязанный поток. Обратитесь к администратору.")
            return

        nxt = await _next_session_for_cohorts(db, cohorts)
        if not nxt:
            await message.answer("Ближайших занятий не найдено.")
            return

    d = datetime.fromisoformat(nxt["date"])
    text = (
        f"Ваше ближайшее занятие: <b>{d.strftime('%d.%m.%Y')} ({_weekday_ru(d)})</b>\n"
        f"Тема занятия: <b>{nxt['title'] or '—'}</b>\n"
        f"Содержание: {nxt['notes'] or '—'}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "Расписание")
async def schedule_dates_only(message: Message, state: FSMContext):
    """Админ — даты всех потоков; участник — только свои. На каждую дату ставим inline‑кнопку."""
    data = await state.get_data()
    user_id  = data.get("user_id") or 0
    nickname = data.get("nickname") or ""

    if not nickname and message.from_user and message.from_user.username:
        nickname = message.from_user.username

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if _is_admin(message, data):
            rows = await (await db.execute(
                """
                SELECT session_id, cohort_id, date
                FROM session_days
                WHERE date >= DATE('now')
                ORDER BY date
                LIMIT 50
                """
            )).fetchall()
        else:
            cohorts = await _user_cohorts(db, user_id, nickname)
            if not cohorts:
                await message.answer("Поток не найден за вашим профилем. Обратитесь к администратору.")
                return
            placeholders = ",".join("?" * len(cohorts))
            rows = await (await db.execute(
                f"""
                SELECT session_id, cohort_id, date
                FROM session_days
                WHERE cohort_id IN ({placeholders}) AND date >= DATE('now')
                ORDER BY date
                LIMIT 30
                """,
                cohorts
            )).fetchall()

    if not rows:
        await message.answer("Ближайших дат нет.")
        return

    lines = ["📅 Даты ближайших занятий:" ]
    kb_rows = []
    for r in rows:
        d = datetime.fromisoformat(r["date"])
        label = d.strftime("%d.%m.%Y")
        lines.append(f"{label} [{r['cohort_id']}]")
        kb_rows.append([InlineKeyboardButton(text=label, callback_data=f"sd:{r['session_id']}:{r['date']}")])

    await message.answer("\n".join(lines),
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))


@router.callback_query(F.data.startswith("sd:"))
async def schedule_date_details(cb: CallbackQuery):
    """По клику на дату показываем тему и краткое содержание конкретной сессии."""
    _, session_id, date_str = cb.data.split(":", 2)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        sess = await (await db.execute(
            "SELECT title, notes FROM course_sessions WHERE id = ?", (int(session_id),)
        )).fetchone()

    d = datetime.fromisoformat(date_str)
    text = (
        f"Дата: <b>{d.strftime('%d.%m.%Y')} ({_weekday_ru(d)})</b>\n"
        f"Тема занятия: <b>{(sess['title'] if sess else '—')}</b>\n"
        f"Содержание: {(sess['notes'] if sess and sess['notes'] else '—')}"
    )
    await cb.message.answer(text, parse_mode="HTML")
    await cb.answer()


def register_admin_info_handlers(dp):
    dp.include_router(router)
