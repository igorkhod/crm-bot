# === Автогенерированный заголовок: crm2/handlers/attendance.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: AttStates
# Функции: attendance_entry, pick_cohort, show_cohort_sessions, enter_attendance, enter_payments, on_pick_session, _mark_kb_att, _mark_kb_pay, mark_attendance, mark_payment
# === Конец автозаголовка
# crm2/handlers/attendance.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
import sqlite3

from crm2.keyboards.admin_attendance import choose_cohort_kb
from crm2.keyboards.session_picker import build_session_picker
from crm2.db.sessions import get_upcoming_sessions_by_cohort, get_recent_past_sessions_by_cohort
from crm2.db.users import list_users_by_cohort
from crm2.db.sqlite import DB_PATH

router = Router(name="attendance")

class AttStates(StatesGroup):
    cohort = State()
    mode = State()           # 'att' | 'pay'
    session = State()        # выбранная сессия (для att/pay)

# --- вход в раздел ---
@router.message(F.text == "📊 Посещение")
async def attendance_entry(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AttStates.cohort)
    await message.answer("Выберите поток:", reply_markup=choose_cohort_kb())

# --- выбор потока ---
@router.message(AttStates.cohort, F.text.in_(["1 поток · набор 09.2023", "2 поток · набор 04.2025"]))
async def pick_cohort(message: Message, state: FSMContext):
    cohort_id = 1 if message.text.startswith("1 поток") else 2
    await state.update_data(cohort_id=cohort_id)
    await message.answer(
        "Поток выбран. Выберите действие:\n"
        "• ✍️ Внести данные — отметить «был/не был»\n"
        "• 💳 Оплата — отметить «оплатил/не оплатил»\n"
        "• 👁 Посмотреть — показать ближайшие занятия",
        reply_markup=choose_cohort_kb()
    )

# --- режимы: внести данные / оплата / посмотреть ---
@router.message(AttStates.cohort, F.text == "👁 Посмотреть")
async def show_cohort_sessions(message: Message, state: FSMContext):
    data = await state.get_data()
    cohort_id = data.get("cohort_id")
    if not cohort_id:
        await message.answer("Сначала выберите поток.")
        return
    sessions = get_upcoming_sessions_by_cohort(cohort_id, limit=10)
    if not sessions:
        await message.answer("Ближайших занятий пока нет.")
        return
    lines = ["Ближайшие занятия выбранного потока:"]
    for s in sessions:
        d1, d2 = s["start_date"], s["end_date"]
        code = (s.get("topic_code") or "").strip()
        dates = f"{d1} — {d2}" if (d1 and d2 and d1 != d2) else (d1 or d2 or "—")
        lines.append("• " + dates + (f" • {code}" if code else ""))
    await message.answer("\n".join(lines))

@router.message(AttStates.cohort, F.text == "✍️ Внести данные")
async def enter_attendance(message: Message, state: FSMContext):
    data = await state.get_data()
    cohort_id = data.get("cohort_id")
    if not cohort_id:
        await message.answer("Сначала выберите поток.")
        return
    await state.set_state(AttStates.mode)
    await state.update_data(mode="att")
    sessions = get_recent_past_sessions_by_cohort(cohort_id, limit=5)
    if not sessions:
        await message.answer("Прошедших занятий не найдено.")
        return
    await message.answer("Выберите прошедшее занятие для отметки посещаемости:", reply_markup=None)
    await message.answer(" ",
                         reply_markup=build_session_picker(sessions, mode="att"))

@router.message(AttStates.cohort, F.text == "💳 Оплата")
async def enter_payments(message: Message, state: FSMContext):
    data = await state.get_data()
    cohort_id = data.get("cohort_id")
    if not cohort_id:
        await message.answer("Сначала выберите поток.")
        return
    await state.set_state(AttStates.mode)
    await state.update_data(mode="pay")
    sessions = get_recent_past_sessions_by_cohort(cohort_id, limit=5)
    if not sessions:
        await message.answer("Прошедших занятий не найдено.")
        return
    await message.answer("Выберите прошедшее занятие для отметки оплаты:", reply_markup=None)
    await message.answer(" ",
                         reply_markup=build_session_picker(sessions, mode="pay"))

# --- выбор сессии (inline) ---
@router.callback_query(F.data.startswith("pick_session:"))
async def on_pick_session(cb: CallbackQuery, state: FSMContext):
    _, mode, sid = cb.data.split(":")
    session_id = int(sid)
    await state.update_data(mode=mode, session_id=session_id)

    data = await state.get_data()
    cohort_id = data.get("cohort_id")
    users = list_users_by_cohort(cohort_id)
    if not users:
        await cb.message.answer("В потоке пока нет пользователей.")
        await cb.answer()
        return

    # по каждому пользователю — кнопки +/-
    header = "Отметка посещаемости" if mode == "att" else "Отметка оплаты"
    await cb.message.answer(f"{header} для занятия #{session_id}:")

    for uid, name in users:
        if mode == "att":
            kb = _mark_kb_att(uid, session_id)
            await cb.message.answer(f"• {name}", reply_markup=kb)
        else:
            kb = _mark_kb_pay(uid, session_id)
            await cb.message.answer(f"• {name}", reply_markup=kb)

    await cb.answer()

# --- inline-кнопки «+/-» ---
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def _mark_kb_att(user_id: int, session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="+ был", callback_data=f"mark:att:present:{user_id}:{session_id}"),
        InlineKeyboardButton(text="- не был", callback_data=f"mark:att:absent:{user_id}:{session_id}"),
        InlineKeyboardButton(text="± опоздал", callback_data=f"mark:att:late:{user_id}:{session_id}"),
    ]])

def _mark_kb_pay(user_id: int, session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="+ оплатил", callback_data=f"mark:pay:1:{user_id}:{session_id}"),
        InlineKeyboardButton(text="- не оплатил", callback_data=f"mark:pay:0:{user_id}:{session_id}"),
    ]])

# --- запись в БД ---
@router.callback_query(F.data.startswith("mark:att:"))
async def mark_attendance(cb: CallbackQuery):
    _, _, status, uid, sid = cb.data.split(":")
    user_id, session_id = int(uid), int(sid)
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO attendance(user_id, session_id, status, noted_by) VALUES (?,?,?,?)",
            (user_id, session_id, status, cb.from_user.id)
        )
        con.commit()
    await cb.answer("Сохранено")
    await cb.message.edit_reply_markup(reply_markup=None)

@router.callback_query(F.data.startswith("mark:pay:"))
async def mark_payment(cb: CallbackQuery):
    _, _, paid, uid, sid = cb.data.split(":")
    user_id, session_id, paid_val = int(uid), int(sid), int(paid)
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO payments(user_id, session_id, paid, noted_by) VALUES (?,?,?,?)",
            (user_id, session_id, paid_val, cb.from_user.id)
        )
        con.commit()
    await cb.answer("Сохранено")
    await cb.message.edit_reply_markup(reply_markup=None)
