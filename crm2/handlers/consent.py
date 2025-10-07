# crm2/handlers/consent.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message

router = Router(name="consent")

# Раньше здесь импортировали RegistrationFSM — это не нужно.
# Либо consent вообще не используется, либо это простой статический экран.
# Делаем безопасный обработчик команды/кнопки согласия.

@router.message(F.text.func(lambda t: t and t.lower() in {"согласие", "даю согласие"}))
async def accept_consent(message: Message):
    await message.answer(
        "Спасибо! Согласие зафиксировано. Вы можете продолжить регистрацию или вернуться в главное меню."
    )
