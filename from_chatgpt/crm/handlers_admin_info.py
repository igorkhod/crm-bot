
from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: CallbackQuery):
    await callback.message.answer("🔧 Здесь будет управление пользователями (удаление, блокировка, назначение ролей).")

@router.callback_query(F.data == "info")
async def info_handler(callback: CallbackQuery):
    await callback.message.answer("📅 Здесь будет отображаться расписание по потокам и ближайшие занятия.")

def register_admin_info_handlers(dp):
    dp.include_router(router)