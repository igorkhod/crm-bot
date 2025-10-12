# crm2/handlers/admin/schedule.py
# Назначение: Обработчики для просмотра расписания в админ-панели (тренинги, мероприятия, целительские приемы)
# Функции:
# - schedule_menu - Входное меню раздела расписания
# - _render_menu - Отображение меню расписания
# - trainings_entry - Вход в раздел тренингов
# - trainings_cohort - Выбор когорты для просмотра тренингов
# - trainings_page - Пагинация списка тренингов
# - _render_trainings - Отображение списка тренингов с пагинацией
# - events_entry - Вход в раздел мероприятий
# - events_page - Пагинация списка мероприятий
# - _render_events - Отображение списка мероприятий с пагинацией
# - healings_entry - Вход в раздел целительских приемов
# - healings_page - Пагинация списка целительских приемов
# - _render_healings - Отображение списка целительских приемов с пагинацией
# - all_entry - Вход в общее расписание
# - all_page - Пагинация общего расписания
# - _render_all - Отображение общего расписания с пагинацией
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from crm2.keyboards.admin_schedule import schedule_menu_kb, schedule_cohorts_kb, pager_kb
from crm2.db import schedule_repo as repo

router = Router(name="admin_schedule")

PAGE = 10

# --- входное меню ---
@router.callback_query(F.data == "admin:schedule")
async def schedule_menu(cb: CallbackQuery):
    await _render_menu(cb)
    await cb.answer()


async def _render_menu(cb: CallbackQuery):  # Принимаем CallbackQuery
    await cb.message.edit_text(
        "🗓 <b>Расписание</b>\nВыберите раздел:",
        reply_markup=schedule_menu_kb(),
        parse_mode="HTML"
    )

# --- 1) Тренинги по потокам ---
@router.callback_query(F.data == "sch:trainings")
async def trainings_entry(cb: CallbackQuery):
    try:
        await cb.message.edit_text("Выберите поток:", reply_markup=schedule_cohorts_kb())
    except TelegramBadRequest:
        await cb.message.answer("Выберите поток:", reply_markup=schedule_cohorts_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("sch:tr:cohort:"))
async def trainings_cohort(cb: CallbackQuery):
    cohort_id = int(cb.data.split(":")[-1])
    await _render_trainings(cb.message, cohort_id, page=1)
    await cb.answer()

@router.callback_query(F.data.startswith("sch:tr:page:"))
async def trainings_page(cb: CallbackQuery):
    # формат: sch:tr:page:<page>:<cohort_id>
    parts = cb.data.split(":")
    page = int(parts[3])
    cohort_id = int(parts[4])
    await _render_trainings(cb.message, cohort_id, page)
    await cb.answer()

async def _render_trainings(msg: Message, cohort_id: int, page: int):
    total = repo.count_trainings(cohort_id)
    pages = max(1, (total + PAGE - 1) // PAGE)
    page = max(1, min(page, pages))
    offset = (page - 1) * PAGE
    items = repo.list_trainings(cohort_id, offset, PAGE)

    lines = [f"🎓 Тренинги — поток {cohort_id} · найдено: {total}", ""]
    for it in items:
        date = it["date"]
        code = it.get("topic_code") or ""
        title = it.get("topic_title") or ""
        sep = " — " if code and title else ""
        lines.append(f"• {date} · {code}{sep}{title}")
    text = "\n".join(lines) if items or total == 0 else "Пока пусто…"

    kb = pager_kb(prefix="sch:tr:page", page=page, pages=pages, suffix=str(cohort_id))
    try:
        await msg.edit_text(text, reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise

# --- 2) Мероприятия ---
@router.callback_query(F.data == "sch:events")
async def events_entry(cb: CallbackQuery):
    await _render_events(cb.message, page=1)
    await cb.answer()

@router.callback_query(F.data.startswith("sch:ev:page:"))
async def events_page(cb: CallbackQuery):
    page = int(cb.data.split(":")[-1])
    await _render_events(cb.message, page)
    await cb.answer()

async def _render_events(msg: Message, page: int):
    total = repo.count_events()
    pages = max(1, (total + PAGE - 1) // PAGE)
    page = max(1, min(page, pages))
    items = repo.list_events(offset=(page - 1) * PAGE, limit=PAGE)

    lines = [f"🎪 Мероприятия · найдено: {total}", ""]
    for it in items:
        lines.append(f"• {it['date']} · {it['title']}")
        if it.get("description"):
            lines.append(f"  {it['description']}")
    text = "\n".join(lines) if items or total == 0 else "Пока пусто…"

    kb = pager_kb(prefix="sch:ev:page", page=page, pages=pages)
    try:
        await msg.edit_text(text, reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise

# --- 3) Целительские приёмы ---
@router.callback_query(F.data == "sch:healings")
async def healings_entry(cb: CallbackQuery):
    await _render_healings(cb.message, page=1)
    await cb.answer()

@router.callback_query(F.data.startswith("sch:hl:page:"))
async def healings_page(cb: CallbackQuery):
    page = int(cb.data.split(":")[-1])
    await _render_healings(cb.message, page)
    await cb.answer()

async def _render_healings(msg: Message, page: int):
    total = repo.count_healings()
    pages = max(1, (total + PAGE - 1) // PAGE)
    page = max(1, min(page, pages))
    items = repo.list_healings(offset=(page - 1) * PAGE, limit=PAGE)

    lines = [f"✨ Целительские приёмы · найдено: {total}", ""]
    for it in items:
        lines.append(f"• {it['date']} {it['time_start']} · {it.get('note','')}".rstrip())
    text = "\n".join(lines) if items or total == 0 else "Пока пусто…"

    kb = pager_kb(prefix="sch:hl:page", page=page, pages=pages)
    try:
        await msg.edit_text(text, reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise

# --- 4) Общее расписание ---
@router.callback_query(F.data == "sch:all")
async def all_entry(cb: CallbackQuery):
    await _render_all(cb.message, page=1)
    await cb.answer()

@router.callback_query(F.data.startswith("sch:all:page:"))
async def all_page(cb: CallbackQuery):
    page = int(cb.data.split(":")[-1])
    await _render_all(cb.message, page)
    await cb.answer()

async def _render_all(msg: Message, page: int):
    total = repo.count_all()
    pages = max(1, (total + PAGE - 1) // PAGE)
    page = max(1, min(page, pages))
    items = repo.list_all(offset=(page - 1) * PAGE, limit=PAGE)

    icon = {"training": "🎓", "event": "🎪", "healing": "✨"}
    lines = [f"📋 Общее расписание · найдено: {total}", ""]
    for it in items:
        k = it["kind"]
        lines.append(f"• {it['start_at']} · {icon.get(k, '•')} {it['title']}")
        if it.get("details"):
            lines.append(f"  {it['details']}")
    text = "\n".join(lines) if items or total == 0 else "Пока пусто…"

    kb = pager_kb(prefix="sch:all:page", page=page, pages=pages)
    try:
        await msg.edit_text(text, reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
