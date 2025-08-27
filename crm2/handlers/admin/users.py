# crm2/handlers/admin/users.py
# Краткая аннотация: подменю "Пользователи" — выбор группы и списки с пагинацией

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from crm2.keyboards.admin_users import users_groups_kb, users_pager_kb
from crm2.db.users_repo import count_users, list_users

router = Router(name="admin_users")

PAGE_SIZE = 10

# Вход из админ-панели (кнопка "👥 Пользователи")
@router.message(StateFilter(None), F.text == "👥 Пользователи")
async def admin_users_entry(message: Message):
    await message.answer("Выберите интересующую вас группу:", reply_markup=users_groups_kb())

# Показать меню групп
@router.callback_query(F.data == "users:groups")
async def admin_users_groups(cb: CallbackQuery):
    await cb.message.edit_text("Выберите интересующую вас группу:", reply_markup=users_groups_kb())
    await cb.answer()

def _group_human(group_key: str) -> str:
    return {
        "stream_1": "1 поток",
        "stream_2": "2 поток",
        "new_intake": "Новый набор",
        "alumni": "Окончившие",
        "admins": "Админы",
    }.get(group_key, group_key)

def _render_users(lines):
    return "\n".join(lines) if lines else "Пока пусто…"

def _user_line(u: dict) -> str:
    full_name = (u.get("full_name") or u.get("nickname") or "—").strip()
    nick = u.get("nickname") or ""
    role = u.get("role") or "user"
    stream = u.get("stream_id") or u.get("cohort_id")
    stream_txt = f" • поток: {stream}" if stream is not None else ""
    nick_txt = f" (@{nick})" if nick else ""
    return f"• {full_name}{nick_txt} — {role}{stream_txt}"

async def _show_group_page(cb_or_msg, group_key: str, page: int):
    total = count_users(group_key)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, pages))
    offset = (page - 1) * PAGE_SIZE
    users = list_users(group_key, offset=offset, limit=PAGE_SIZE)
    lines = [f"<b>{_group_human(group_key)}</b> — найдено: {total}", ""]
    lines += [_user_line(u) for u in users]
    text = _render_users(lines)
    kb = users_pager_kb(group_key, page, pages)
    # поддержим и message, и callback.message
    msg = getattr(cb_or_msg, "message", None) or cb_or_msg
    await msg.edit_text(text, reply_markup=kb)

# Выбор группы → страница 1
@router.callback_query(F.data.startswith("users:group:"))
async def admin_users_pick_group(cb: CallbackQuery):
    group_key = cb.data.split(":", 2)[-1]
    await _show_group_page(cb, group_key=group_key, page=1)
    await cb.answer()

# Переход по страницам
@router.callback_query(F.data.startswith("users:page:"))
async def admin_users_page(cb: CallbackQuery):
    _, _, group_key, page_str = cb.data.split(":", 3)
    try:
        page = int(page_str)
    except ValueError:
        page = 1
    await _show_group_page(cb, group_key=group_key, page=page)
    await cb.answer()
