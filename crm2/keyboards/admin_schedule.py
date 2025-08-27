# crm2/keyboards/admin_schedule.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def schedule_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎓 По потокам", callback_data="sch:trainings")
    kb.button(text="🎪 Мероприятия", callback_data="sch:events")
    kb.button(text="✨ Приёмы",     callback_data="sch:healings")
    kb.button(text="📋 Общее",      callback_data="sch:all")
    kb.button(text="⬅️ В админ-панель", callback_data="admin:back")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

def schedule_streams_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="1 поток", callback_data="sch:tr:stream:1")
    kb.button(text="2 поток", callback_data="sch:tr:stream:2")
    kb.button(text="⬅️ Назад", callback_data="adm:schedule")
    kb.adjust(2, 1)
    return kb.as_markup()

def pager_kb(prefix: str, page: int, pages: int, suffix: str = "") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    prev_p = max(1, page - 1)
    next_p = min(pages, page + 1)
    # prefix: 'sch:tr:page:1'  (если есть суффикс, например stream_id)
    if suffix:
        kb.button(text="◀️", callback_data=f"{prefix}:{prev_p}:{suffix}")
        kb.button(text=f"{page}/{pages}", callback_data="noop")
        kb.button(text="▶️", callback_data=f"{prefix}:{next_p}:{suffix}")
    else:
        kb.button(text="◀️", callback_data=f"{prefix}:{prev_p}")
        kb.button(text=f"{page}/{pages}", callback_data="noop")
        kb.button(text="▶️", callback_data=f"{prefix}:{next_p}")
    kb.button(text="⬅️ Меню расписания", callback_data="adm:schedule")
    kb.button(text="⬅️ В админ-панель",   callback_data="admin:back")
    kb.adjust(3, 2)
    return kb.as_markup()
