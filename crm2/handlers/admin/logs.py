# crm2/handlers/admin/logs.py
"""
Модуль logs.py - просмотр логов рассылок и статистики в админ-панели

Назначение: предоставляет функционал для просмотра статистики рассылок
Функции:
- logs_menu_kb - создание клавиатуры меню логов
- logs_overview - показ последних рассылок с их статистикой (отправлено/всего/ошибки)
- back_to_admin_panel - возврат в главное меню админ-панели
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import json

from crm2.utils.guards import AdminOnly
from crm2.db.core import get_db_connection

router = Router()
router.message.filter(AdminOnly())
router.callback_query.filter(AdminOnly())


def logs_menu_kb():
    """Создание клавиатуры меню логов"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="adm:logs")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="adm:logs_back")],
    ])


def safe_json_parse(json_str: str) -> dict:
    """Безопасный парсинг JSON строки"""
    try:
        return json.loads(json_str) if json_str else {}
    except (json.JSONDecodeError, TypeError):
        return {}


@router.callback_query(F.data == "adm:logs")
async def logs_overview(cb: CallbackQuery):
    """Показ последних рассылок с их статистикой"""
    try:
        with get_db_connection() as con:
            last_bc = con.execute("""
                                  SELECT id,
                                         title,
                                         datetime(COALESCE(sent_at, created_at)) as sent_time,
                                         COALESCE(stats_json, '{}')              as stats
                                  FROM broadcasts
                                  ORDER BY COALESCE(sent_at, created_at) DESC LIMIT 5
                                  """).fetchall()

        if not last_bc:
            await cb.message.answer("📊 Пока нет логов рассылок.", reply_markup=logs_menu_kb())
            await cb.answer()
            return

        lines = ["📊 **Последние рассылки:**\n"]
        for bid, title, sent_time, stats_json in last_bc:
            stats = safe_json_parse(stats_json)
            sent_count = stats.get('sent', 0)
            total_count = stats.get('total', 0)
            failed_count = stats.get('failed', 0)

            status_emoji = "✅" if sent_count == total_count and total_count > 0 else "🔄"
            lines.append(
                f"{status_emoji} **#{bid}** • {title or 'Без названия'}\n"
                f"⏰ {sent_time} • 📨 {sent_count}/{total_count} • ❌ {failed_count}\n"
            )

        text = "\n".join(lines)

        try:
            await cb.message.edit_text(text, reply_markup=logs_menu_kb())
        except TelegramBadRequest:
            # Если сообщение слишком длинное, отправляем новое
            await cb.message.answer(text, reply_markup=logs_menu_kb())

        await cb.answer()

    except Exception as e:
        error_text = f"❌ Ошибка при получении логов: {str(e)}"
        await cb.message.answer(error_text, reply_markup=logs_menu_kb())
        await cb.answer()


@router.callback_query(F.data == "adm:logs_back")
async def back_to_admin_panel(cb: CallbackQuery):
    """Возврат в главное меню админ-панели"""
    try:
        from crm2.handlers.admin.panel import open_admin_menu
        await open_admin_menu(cb.message)
        await cb.answer()
    except Exception as e:
        await cb.message.answer(f"❌ Ошибка возврата: {str(e)}")
        await cb.answer()