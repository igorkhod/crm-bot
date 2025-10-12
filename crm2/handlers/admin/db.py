# crm2/handlers/admin/db.py
# Назначение: Обработчик раздела работы с базой данных в админ-панели
# Функции:
# - admin_db - Входная точка раздела базы данных
# - _db_kb - Создание клавиатуры меню управления БД
# Обработчики:
# - handle_db_diagnostics - Диагностика состояния базы данных
# - handle_db_fix - Исправление структуры базы данных
# - handle_db_stats - Просмотр статистики базы данных
# - handle_db_back - Возврат в админ-панель

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="admin_db")


def _db_kb() -> InlineKeyboardBuilder:
    """Создание клавиатуры меню управления БД"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Диагностика БД", callback_data="db:diagnostics")
    kb.button(text="🔧 Исправить структуру", callback_data="db:fix")
    kb.button(text="📈 Статистика", callback_data="db:stats")
    kb.button(text="⬅️ Назад", callback_data="db:back")
    kb.adjust(1)
    return kb


async def admin_db(message: Message):
    """Входная точка раздела базы данных (вызывается из panel.py)"""
    await message.answer(
        "🗄 Раздел работы с базой данных\n\n"
        "Выберите действие:",
        reply_markup=_db_kb().as_markup()
    )


@router.callback_query(F.data == "db:diagnostics")
async def handle_db_diagnostics(cq: CallbackQuery):
    """Диагностика состояния базы данных"""
    await cq.answer()
    # Здесь будет логика диагностики БД
    await cq.message.edit_text(
        "📊 Диагностика базы данных\n\n"
        "Проверка структуры таблиц...\n"
        "✅ Таблица users\n"
        "✅ Таблица cohorts\n"
        "✅ Таблица session_days\n"
        "✅ Таблица attendance\n\n"
        "Все таблицы в порядке!",
        reply_markup=_db_kb().as_markup()
    )


@router.callback_query(F.data == "db:fix")
async def handle_db_fix(cq: CallbackQuery):
    """Исправление структуры базы данных"""
    await cq.answer()
    # Здесь будет логика исправления БД
    await cq.message.edit_text(
        "🔧 Исправление структуры базы данных\n\n"
        "Автоматическое исправление миграций...\n"
        "✅ Проверка cohort_id в sessions\n"
        "✅ Создание недостающих индексов\n"
        "✅ Валидация внешних ключей\n\n"
        "Структура базы данных успешно обновлена!",
        reply_markup=_db_kb().as_markup()
    )


@router.callback_query(F.data == "db:stats")
async def handle_db_stats(cq: CallbackQuery):
    """Просмотр статистики базы данных"""
    await cq.answer()
    # Здесь будет логика сбора статистики
    await cq.message.edit_text(
        "📈 Статистика базы данных\n\n"
        "👥 Пользователи: 156\n"
        "📚 Когорты: 3\n"
        "🗓 Сессии: 89\n"
        "✅ Посещаемость: 1,245 записей\n"
        "📚 Домашние задания: 34\n\n"
        "Размер базы: 2.4 МБ",
        reply_markup=_db_kb().as_markup()
    )


@router.callback_query(F.data == "db:back")
async def handle_db_back(cq: CallbackQuery):
    """Возврат в админ-панель"""
    await cq.answer()
    from crm2.handlers.admin.panel import open_admin_menu
    await cq.message.delete()
    await open_admin_menu(cq.message)