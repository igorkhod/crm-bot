# crm2/keyboards/project.py
# Назначение: Inline-клавиатура информации о проекте с внешними ссылками
# Функции:
# - project_menu_kb - Меню проекта с ссылками на режим занятий и смыслы проекта
from aiogram.utils.keyboard import InlineKeyboardBuilder

def project_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Режим проведения занятий",
        url="https://www.krasnpsytech.ru/texts/mode.html"
    )
    kb.button(
        text="Смыслы, заложенные в проекте",
        url="https://www.krasnpsytech.ru/texts/meaning.html"
    )
    kb.button(
        text="↩️ Главное меню",
        callback_data="info:mainmenu"
    )
    kb.adjust(1)
    return kb.as_markup()
