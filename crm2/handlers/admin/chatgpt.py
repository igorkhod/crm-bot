# 📄 crm2/handlers/admin/chatgpt.py
# chatgpt
# Назначение: обработчик кнопки «🤖 ChatGPT» в админ-панели.
# Что делает:
# принимает нажатие на inline-кнопку adm:chatgpt_status;
# вызывает сервис probe_paid_access() для диагностики доступа к ChatGPT;
# формирует и отправляет администратору результат проверки в Markdown (🟢 открыт / 🔴 закрыт / 🟡 не определён).
# Расположение:
# crm2/
#  └── handlers/
#       └── admin/
#            └── chatgpt.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from crm2.services.chatgpt_status import probe_paid_access, render_binary_md

router = Router(name="admin_chatgpt")

@router.callback_query(F.data == "adm:chatgpt_status")
async def admin_chatgpt_entry(cb: CallbackQuery):
    d = probe_paid_access()
    await cb.message.edit_text(render_binary_md(d), parse_mode="Markdown")
    await cb.answer()
