# crm2/handlers/attendance.py
from __future__ import annotations
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from crm2.keyboards.admin_attendance import choose_stream_kb
from crm2.db.sessions import get_upcoming_sessions_by_stream

router = Router(name="attendance")

class AttStates(StatesGroup):
    stream = State()

@router.message(F.text == "📊 Посещение")
async def attendance_entry(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AttStates.stream)
    await message.answer("Выберите поток:", reply_markup=choose_stream_kb())

@router.message(AttStates.stream, F.text.in_(["1 поток · набор 09.2023", "2 поток · набор 04.2025"]))
async def pick_stream(message: Message, state: FSMContext):
    stream_id = 1 if message.text.startswith("1 поток") else 2
    await state.update_data(stream_id=stream_id)
    await message.answer("Поток выбран. Нажмите «👁 Посмотреть», чтобы увидеть ближайшие занятия.")

@router.message(AttStates.stream, F.text == "👁 Посмотреть")
async def show_stream_sessions(message: Message, state: FSMContext):
    data = await state.get_data()
    stream_id = data.get("stream_id")
    if not stream_id:
        await message.answer("Сначала выберите поток.")
        return
    sessions = get_upcoming_sessions_by_stream(stream_id, limit=10)
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
