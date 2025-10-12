# crm2/handlers/admin/chatgpt.py
# Назначение: Обработчик кнопки «🤖 ChatGPT» в админ-панели для проверки статуса доступа
# Функции:
# - admin_chatgpt_entry - Проверка статуса доступа к ChatGPT и отправка результата администратору
from aiogram import Router, F
from aiogram.types import CallbackQuery
from crm2.services.chatgpt_status import probe_paid_access, render_binary_md

router = Router(name="admin_chatgpt")

@router.callback_query(F.data == "adm:chatgpt_status")
async def admin_chatgpt_entry(cb: CallbackQuery):
    d = probe_paid_access()
    await cb.message.edit_text(render_binary_md(d), parse_mode="Markdown")
    await cb.answer()
