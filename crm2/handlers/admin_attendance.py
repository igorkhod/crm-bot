# crm2/handlers/admin_attendance.py
from aiogram import Router, F
from aiogram.types import Message
from crm2.services import attendance
from crm2.app import bot

router = Router()

@router.message(F.text.startswith("/homework_send"))
async def send_homework(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Используй: /homework_send <session_id> <ссылка>")
        return

    session_id = int(parts[1])
    link = parts[2]

    user_ids = await attendance.get_present_users(session_id)
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, f"📚 Домашнее задание:\n{link}")
            sent += 1
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить {uid}: {e}")

    await message.answer(f"✅ Отправлено {sent} курсантам, присутствовавшим на занятии {session_id}")
