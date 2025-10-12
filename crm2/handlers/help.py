# crm2/handlers/help.py
# Назначение: Обработчик справки по системе с описанием всех доступных функций бота
# Функции:
# - cmd_help - Отправка структурированной справки по команде /help
# Обработчики:
# - cmd_help - Основной обработчик команды /help с Markdown-форматированием
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "🤖 *CRM-бот Psytech — справка*\n\n"
        "📅 *Расписание* — подменю выбора потока, наборов и мероприятий\n"
        "📚 *Материалы* — доступ к учебным материалам\n"
        "ℹ️ *Профиль* — личный кабинет курсанта\n"
        "🤖 *ИИ-агенты* — подменю с ассистентами (требуется VPN)\n"
        "⚙️ *Админ* — панель управления (только для админов)\n"
        "↩️ *Выйти в меню* — возврат к экрану входа/регистрации\n\n"
        "ℹ️ Команда */help* всегда доступна."
    )
    await message.answer(text, parse_mode="Markdown")
