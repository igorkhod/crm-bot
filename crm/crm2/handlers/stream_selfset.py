# crm2/handlers/stream_selfset.py
from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.services.participants import get_streams, upsert_participant_stream, get_user_id_by_tg

router = Router()


def _streams_kb(prefix: str = "me:setstream:"):
    kb = InlineKeyboardBuilder()
    streams = get_streams()
    if not streams:
        # На случай пустой таблицы – предлагаем базовые варианты
        streams = [(1, "Поток 1"), (2, "Поток 2")]
    for sid, title in streams:
        kb.button(text=title, callback_data=f"{prefix}{sid}")
    kb.adjust(2)
    return kb


@router.message(F.text.in_({"/set_stream", "Выбрать поток"}))
async def cmd_set_stream(message: Message):
    await message.answer(
        "Выберите свой поток:\n"
        "— это нужно, чтобы учитывать посещаемость и рассылать ДЗ по вашему потоку.",
        reply_markup=_streams_kb().as_markup(),
    )


@router.callback_query(F.data.startswith("me:setstream:"))
async def me_set_stream(cq: CallbackQuery):
    try:
        stream_id = int(cq.data.split(":")[2])
    except Exception:
        await cq.answer("Некорректные данные", show_alert=True)
        return

    tg_id = cq.from_user.id
    user_id = get_user_id_by_tg(tg_id)
    if not user_id:
        await cq.answer("Вы ещё не зарегистрированы в боте.", show_alert=True)
        return

    upsert_participant_stream(user_id, stream_id)
    await cq.message.answer(f"✅ Поток установлен: {stream_id}. Спасибо!")
    await cq.answer()


# ⤵️ Этот хендлер позволяет открыть выбор потока из «Личного кабинета»
@router.callback_query(F.data == "profile:set_stream")
async def open_set_stream_from_profile(cq: CallbackQuery):
    await cq.message.answer(
        "Выберите свой поток:",
        reply_markup=_streams_kb().as_markup(),
    )
    await cq.answer()
