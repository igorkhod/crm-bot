from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from crm2.services.attendance import (
    get_sessions_near,
    get_not_yet_delivered,
    mark_homework_delivered,
)

router = Router()

# --------- FSM ---------

class HW(StatesGroup):
    awaiting_link = State()
    chosen_session = State()

# --------- helpers ---------

def _kb(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def homework_menu_markup() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📅 Выбрать занятие", callback_data="hw:list")],
        [InlineKeyboardButton(text="🧾 Статус по занятию", callback_data="hw:status")],
        [InlineKeyboardButton(text="♻️ Сбросить отметки (опасно)", callback_data="hw:reset")],
        [InlineKeyboardButton(text="⬅️ Назад в админ-меню", callback_data="admin:back")],
    ]
    return _kb(rows)

def _sessions_list_kb(sessions: Iterable[tuple[int, str, int | None, str | None]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for sid, sdate, stream_id, topic_code in sessions:
        title = f"{sdate} · поток {stream_id or '—'} · {topic_code or '…'}"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"hw:session:{sid}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="hw:menu")])
    return _kb(rows)

def _session_actions_kb(session_id: int) -> InlineKeyboardMarkup:
    return _kb([
        [InlineKeyboardButton(text="🚀 Отправить ДЗ (ввести ссылку)", callback_data=f"hw:send:{session_id}")],
        [InlineKeyboardButton(text="🧾 Статус доставок", callback_data=f"hw:status:{session_id}")],
        [InlineKeyboardButton(text="⬅️ К списку занятий", callback_data="hw:list")],
        [InlineKeyboardButton(text="⬅️ Назад в админ-меню", callback_data="admin:back")],
    ])

# --------- message handlers ---------

@router.message(F.text == "📚 Домашние задания")
async def admin_homework_entry(message: Message):
    await message.answer("Раздел «Домашние задания».", reply_markup=homework_menu_markup())

# --------- callbacks ---------

@router.callback_query(F.data == "hw:menu")
async def cb_hw_menu(cb: CallbackQuery):
    await cb.message.edit_text("Раздел «Домашние задания».", reply_markup=homework_menu_markup())
    await cb.answer()

@router.callback_query(F.data == "hw:list")
async def cb_hw_list(cb: CallbackQuery):
    rows = await get_sessions_near(days=14)
    if not rows:
        await cb.message.edit_text("Ближайших занятий не найдено.", reply_markup=homework_menu_markup())
        return await cb.answer()
    await cb.message.edit_text("Выбери занятие для рассылки ДЗ:", reply_markup=_sessions_list_kb(rows))
    await cb.answer()

@router.callback_query(F.data.startswith("hw:session:"))
async def cb_hw_session(cb: CallbackQuery):
    session_id = int(cb.data.split(":")[2])
    await cb.message.edit_text(f"Занятие #{session_id}.", reply_markup=_session_actions_kb(session_id))
    await cb.answer()

# --- отправка ДЗ ---

@router.callback_query(F.data.startswith("hw:send:"))
async def cb_hw_send_ask_link(cb: CallbackQuery, state: FSMContext):
    session_id = int(cb.data.split(":")[2])
    await state.set_state(HW.awaiting_link)
    await state.update_data(session_id=session_id)
    await cb.message.edit_text(
        f"Занятие #{session_id}.\n"
        "Вставь ссылку(и) на Я.Диск одной строкой (можно несколько через пробел / переносы строк).",
        reply_markup=_kb([[InlineKeyboardButton(text="❌ Отмена", callback_data=f"hw:session:{session_id}")]])
    )
    await cb.answer()

@router.message(HW.awaiting_link)
async def hw_got_links(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id: int = data["session_id"]

    # распарсим все URL из текста
    links = [x.strip() for x in message.text.replace("\n", " ").split() if x.strip()]
    if not links:
        await message.answer("Не нашёл ссылок. Пришли строку(и) с URL.")
        return

    # Кому слать: присутствовавшие и ещё не получавшие
    user_ids = await get_not_yet_delivered(session_id)
    if not user_ids:
        await message.answer("Никто не отмечен «присутствовал», либо всем уже отправляли.")
        await state.clear()
        return

    sent = 0
    for uid in user_ids:
        text = "📚 Домашнее задание:\n" + "\n".join(links)
        try:
            await message.bot.send_message(uid, text)
            # отметим доставку (берём первую ссылку как «основную»)
            await mark_homework_delivered(session_id, uid, link=links[0])
            sent += 1
            await asyncio.sleep(0.05)  # не душим API
        except Exception as e:
            logging.warning("HW delivery failed: user=%s err=%r", uid, e)

    await message.answer(f"Готово: отправлено {sent} из {len(user_ids)} пользователям.")
    await state.clear()
    # назад к карточке занятия
    await message.answer(f"Занятие #{session_id}.", reply_markup=_session_actions_kb(session_id))

# --- статус/сброс (заглушки безопасные) ---

@router.callback_query(F.data == "hw:status")
async def cb_hw_status_ask(cb: CallbackQuery):
    await cb.message.edit_text("Выбери занятие в «📅 Выбрать занятие», а потом нажми «🧾 Статус доставок».",
                               reply_markup=homework_menu_markup())
    await cb.answer()

@router.callback_query(F.data.startswith("hw:status:"))
async def cb_hw_status(cb: CallbackQuery):
    session_id = int(cb.data.split(":")[2])
    # Мини-отчёт: сколько ещё не получили
    pending = await get_not_yet_delivered(session_id)
    got = "—" if pending is None else f"Ещё не получили: {len(pending)}"
    await cb.message.edit_text(f"Статус по занятию #{session_id}.\n{got}",
                               reply_markup=_session_actions_kb(session_id))
    await cb.answer()

@router.callback_query(F.data == "hw:reset")
async def cb_hw_reset_info(cb: CallbackQuery):
    await cb.message.edit_text("Сброс отметок — функционал заглушка. Реализуем после согласования.",
                               reply_markup=homework_menu_markup())
    await cb.answer()
