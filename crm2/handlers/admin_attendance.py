# crm2/handlers/admin_attendance.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from crm2.bot import bot     # ✅ берём бота из отдельного модуля
from crm2.db import db
from crm2.services import attendance

router = Router()

# ---------------- Меню раздела: Посещаемость ----------------

async def show_attendance_menu(message: Message):
    rows = await db.fetch_all(
        "SELECT id, date, topic_code, stream_id FROM session_days ORDER BY date DESC LIMIT 20"
    )
    if not rows:
        await message.answer("Нет занятий в базе.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{r[1]} • {r[2] or '-'} • Stream:{r[3]}",
            callback_data=f"att_sess:{r[0]}")]
        for r in rows
    ])
    await message.answer("📋 Выберите занятие для отметки:", reply_markup=kb)


@router.callback_query(F.data.startswith("att_sess:"))
async def open_attendance_for_session(cb: CallbackQuery):
    session_id = int(cb.data.split(":")[1])

    users = await db.fetch_all("""
        SELECT u.id, COALESCE(u.full_name, u.nickname, u.username, u.phone, CAST(u.id AS TEXT)) AS label
        FROM users u
        WHERE u.role='user'
        ORDER BY label
    """)

    if not users:
        await cb.message.edit_text("Курсанты не найдены.")
        await cb.answer()
        return

    kb_rows = []
    for uid, label in users:
        kb_rows.append([
            InlineKeyboardButton(text=f"✅ {label}", callback_data=f"att:{uid}:{session_id}:present"),
            InlineKeyboardButton(text="❌", callback_data=f"att:{uid}:{session_id}:absent"),
        ])

    await cb.message.edit_text(
        f"Занятие SID={session_id} — отметьте посещаемость:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("att:"))
async def mark_attendance_action(cb: CallbackQuery):
    _, uid, session_id, status = cb.data.split(":")
    await attendance.mark_attendance(int(uid), int(session_id), status, cb.from_user.id)
    await cb.answer(f"Сохранено: {status}")

# ---------------- Меню раздела: Домашние задания ----------------

async def show_homework_menu(message: Message):
    rows = await db.fetch_all(
        "SELECT id, date, topic_code, stream_id FROM session_days ORDER BY date DESC LIMIT 20"
    )
    if not rows:
        await message.answer("Нет занятий в базе.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{r[1]} • {r[2] or '-'} • Stream:{r[3]}",
            callback_data=f"hw_sess:{r[0]}")]
        for r in rows
    ])
    await message.answer("📚 Выберите занятие для рассылки ДЗ:", reply_markup=kb)


@router.callback_query(F.data.startswith("hw_sess:"))
async def request_homework_link(cb: CallbackQuery):
    session_id = int(cb.data.split(":")[1])
    await cb.message.edit_text(
        f"Вставьте ссылку на ДЗ для занятия SID={session_id}:\n"
        f"Используйте команду:\n"
        f"/homework_send {session_id} <ссылка_на_ЯндексДиск>"
    )
    await cb.answer()


@router.message(F.text.startswith("/homework_send"))
async def send_homework(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Используй: /homework_send <session_id> <ссылка>")
        return

    session_id = int(parts[1])
    link = parts[2]

    await attendance.ensure_homework_delivery_table()

    # только тем, кто был present и ещё не получал материалы
    user_ids = await attendance.get_not_yet_delivered(session_id)
    if not user_ids:
        await message.answer("👌 Все присутствовавшие уже получили материалы.")
        return

    ok = fail = 0
    for uid in user_ids:
        try:
            # Можно использовать и message.bot, но здесь у нас импортирован глобальный bot.
            await bot.send_message(uid, f"📚 Домашнее задание по занятию {session_id}:\n{link}")
            await attendance.mark_homework_delivered(session_id, uid, link)
            ok += 1
        except Exception as e:
            fail += 1
            await message.answer(f"⚠️ {uid}: {e}")

    await message.answer(f"📤 ДЗ отправлено: {ok}; ошибок: {fail}")
