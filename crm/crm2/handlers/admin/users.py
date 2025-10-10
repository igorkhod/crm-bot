# === Автогенерированный заголовок: crm2/handlers/admin/users.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: admin_users_entry, admin_users_groups, _group_human, _user_line, _show_group_page, admin_users_pick_group, admin_users_page, admin_back
# === Конец автозаголовка
# crm2/handlers/admin/users.py
# Краткая аннотация: подменю "Пользователи" — выбор группы и списки с пагинацией

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from crm2.keyboards.admin_users import users_groups_kb, users_pager_kb
from crm2.db.users_repo import count_users, list_users
from aiogram.exceptions import TelegramBadRequest

router = Router(name="admin_users")

PAGE_SIZE = 10


# Вход из админ-панели (кнопка "👥 Пользователи")
@router.message(StateFilter(None), F.text == "👥 Пользователи")
async def admin_users_entry(message: Message):
    await message.answer("Выберите интересующую вас группу:", reply_markup=users_groups_kb())


# Показать только меню групп (кнопка "🔄 Выбрать группу")
@router.callback_query(F.data == "users:groups")
async def admin_users_groups(cb: CallbackQuery):
    await cb.message.edit_text("Выберите интересующую вас группу:", reply_markup=users_groups_kb())
    await cb.answer()


def _group_human(group_key: str) -> str:
    return {
        "cohort_1": "1 поток",
        "cohort_2": "2 поток",
        "new_intake": "Новый набор",
        "alumni": "Окончившие",
        "admins": "Админы",
    }.get(group_key, group_key)


def _user_line(u: dict) -> str:
    name = (u.get("full_name") or u.get("nickname") or "—").strip()
    nick = u.get("nickname") or ""
    role = u.get("role") or "user"
    cohort = u.get("cohort_id") or u.get("cohort_id")
    nick_txt = f" (@{nick})" if nick else ""
    cohort_txt = f" • поток: {cohort}" if cohort is not None else ""
    return f"• {name}{nick_txt} — {role}{cohort_txt}"


async def _show_group_page(cb_or_msg, group_key: str, page: int):
    total = count_users(group_key)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, pages))
    offset = (page - 1) * PAGE_SIZE
    users = list_users(group_key, offset=offset, limit=PAGE_SIZE)

    lines = [f"<b>{_group_human(group_key)}</b> — найдено: {total}", ""]
    lines += [_user_line(u) for u in users]
    text = "\n".join(lines) if users or total == 0 else "Пока пусто…"

    kb = users_pager_kb(group_key, page, pages)
    # Поддержка и callback.message, и обычного message
    msg = getattr(cb_or_msg, "message", None) or cb_or_msg
    try:
       await msg.edit_text(text, reply_markup=kb)
    except TelegramBadRequest as e:
        # Если контент не изменился (например, жмём ◀️/▶️ при 1/1),
        # просто тихо отвечаем на колбэк, чтобы не было ошибки в логах.
        if "message is not modified" in str(e).lower():
            # если это callback — ответим, чтобы убрать «часики»
            if hasattr(cb_or_msg, "answer"):
                try:
                    await cb_or_msg.answer("Уже на этой странице")
                except Exception:
                    pass
            return
        raise


# Выбор группы → страница 1
@router.callback_query(F.data.startswith("users:group:"))
async def admin_users_pick_group(cb: CallbackQuery):
    # было: cb.data.split(":", 2)[-1] → давало "group"
    group_key = cb.data.split(":")[-1]  # теперь корректно: cohort_1 / cohort_2 / new_intake / alumni / admins
    await _show_group_page(cb, group_key=group_key, page=1)
    await cb.answer()


# Переход по страницам
@router.callback_query(F.data.startswith("users:page:"))
async def admin_users_page(cb: CallbackQuery):
    # формат: users:page:<group_key>:<page>
    parts = cb.data.split(":")
    group_key = parts[2] if len(parts) >= 4 else "cohort_1"
    try:
        page = int(parts[3])
    except Exception:
        page = 1
    await _show_group_page(cb, group_key=group_key, page=page)
    await cb.answer()


# хендлер «назад»:

@router.callback_query(F.data == "admin:back")
async def admin_back(cb: CallbackQuery):
    """
    Возврат из списка пользователей в админ-панель.
    Пытаемся отрендерить встроенную панель, иначе просто отвечаем текстом.
    """
    try:
        # Если у тебя есть готовый рендерер панели — используем его.
        from crm2.handlers.admin.panel import render_admin_panel  # см. шаг 2
        await render_admin_panel(cb.message)
    except Exception:
        # Фолбэк: убираем инлайн и пишем подсказку.
        try:
            await cb.message.edit_text("Админ-панель:")
        except TelegramBadRequest:
            await cb.message.answer("Админ-панель:")
    finally:
        await cb.answer()

#         конец файла  crm2/handlers/admin/users.py
