# === crm2/handlers/start.py ===
from aiogram import Router, types
from aiogram.filters import CommandStart
from crm2.db.users import get_user_by_tg
from crm2.keyboards._impl import guest_start_kb, role_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    """
    /start
    - Гость: показываем приветствие и гостевое меню (Войти / Регистрация / О проекте).
    - Зарегистрированный: сразу попадаем в главное меню (без авто-перехода в расписание).
    """
    tg_id = message.from_user.id

    # Пытаемся найти пользователя в БД
    user = await get_user_by_tg(tg_id)

    # --- Гость ---
    if user is None:
        await message.answer(
            "Добро пожаловать в *Psytech*! 🌌\n"
            "Вы можете войти, зарегистрироваться или сначала узнать о проекте.",
            reply_markup=guest_start_kb(),
            parse_mode="Markdown",
        )
        return

    # --- Зарегистрированный пользователь ---
    role = (user.get("role") or "user").strip()
    await message.answer(
        f"Главное меню (ваша роль: {role})",
        reply_markup=role_kb(role),
    )
