# crm2/keyboards/main_menu.py
from aiogram.types import KeyboardButton
from ._impl import guest_start_kb as _guest_start_kb, role_kb as _role_kb

def guest_start_kb():
    return _guest_start_kb()

def role_kb(role: str):
    return _role_kb(role)

KeyboardButton(text="🩺 DB Doctor")