# crm2/handlers/admin_attendance.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from crm2.services import attendance

router = Router()


# --- Меню посещаемости ---

@router.message(F.text == "/attendance")
async def show_attendance_menu(message: Message):
    sessions = await attendance.get_sessions_near()
    if not sessions:
        await message.answer("Нет ближайших занятий.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{row[1]} [{row[3]}]", callback_data=f"att_sess:{row[0]}")]
            for row in sessions
        ]
    )
    await message.answer("Выбери занятие для отметки посещаемости:", reply_markup=kb)


@router.callback_query(F.data.startswith("att_sess:"))
async def choose_session(callback: CallbackQuery):
    session_id = int(callback.data.split(":")[1])
    # Получаем список курсантов
    rows = await callback.bot.db.fetch_all(
        "SELECT id, nickname, full_name FROM users ORDER BY full_name"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ {r[2]}", callback_data=f"att:{session_id}:{r[0]}:present"
                ),
                InlineKeyboardButton(
                    text=f"❌ {r[2]}", callback_data=f"att:{session_id}:{r[0]}:absent"
                ),
            ]
            for r in rows
        ]
    )
    await callback.message.answer(f"Отметка посещаемости (session_id={session_id}):", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("att:"))
async def mark_attendance_cb(callback: CallbackQuery):
    _, session_id, user_id, status = callback.data.split(":")
    await attendance.mark_attendance(int(user_id), int(session_id), status, callback.from_user.id)
    await callback.answer(f"✅ Отметил: {status}")


# --- Домашние задания ---

@router.message(F.text == "/homework")
async def show_homework_menu(message: Message):
    sessions = await attendance.get_sessions_near()
    if not sessions:
        await message.answer("Нет ближайших занятий.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{row[1]} [{row[3]}]", callback_data=f"hw_sess:{row[0]}")]
            for row in sessions
        ]
    )
    await message.answer("Выбери занятие для рассылки ДЗ:", reply_markup=kb)


@router.callback_query(F.data.startswith("hw_sess:"))
async def choose_homework_session(callback: CallbackQuery):
    session_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        f"Чтобы отправить ДЗ:\n"
        f"/homework_send {session_id} <ссылка_на_ЯндексДиск>"
    )
    await callback.answer()


@router.message(F.text.startswith("/homework_send"))
async def send_homework(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Используй: /homework_send <session_id> <ссылка>")
        return

    session_id = int(parts[1])
    link = parts[2]

    user_ids = await attendance.get_not_yet_delivered(session_id)
    sent = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, f"📚 Домашнее задание:\n{link}")
            await attendance.mark_homework_delivered(session_id, uid, link)
            sent += 1
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить {uid}: {e}")

    await message.answer(f"✅ Отправлено {sent} курсантам (session_id={session_id})")
