# crm2/handlers/admin/attendance.py
from __future__ import annotations

import logging
from datetime import date, datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from crm2.services.database import db
from crm2.services.users import get_user_by_telegram

logger = logging.getLogger(__name__)
router = Router()

ATTENDANCE_STATUSES = {
    'not_set': '⚪ Не отмечен',
    'present': '✅ Присутствовал',
    'absent': '❌ Отсутствовал',
    'stopped': '⏸ Прекратил занятия',
    'expelled': '🚫 Отчислен'
}


async def admin_attendance_entry(cq: CallbackQuery):
    """Входная точка раздела посещаемости из админ-панели"""
    await cq.answer()
    await show_attendance_main(cq.message)


async def show_attendance_main(message: Message):
    """Показывает главное меню посещаемости с учетом сегодняшней даты"""
    today = date.today().isoformat()

    today_cohorts = await db.fetch_all("""
                                       SELECT DISTINCT c.id, c.name
                                       FROM session_days sd
                                                JOIN cohorts c ON sd.cohort_id = c.id
                                       WHERE sd.date = ?
                                       """, (today,))

    kb = InlineKeyboardBuilder()

    if today_cohorts:
        text = f"📅 Сегодня {date.today().strftime('%d.%m.%Y')} есть занятия:\n"
        for cohort in today_cohorts:
            text += f"• {cohort['name']}\n"
            kb.button(text=f"📝 {cohort['name']}", callback_data=f"attendance:cohort:{cohort['id']}:{today}")

        text += "\nВыберите группу для отметки или другую группу:"
        kb.button(text="🔍 Выбрать другую группу", callback_data="attendance:choose_cohort")
    else:
        text = f"📅 Сегодня {date.today().strftime('%d.%m.%Y')} занятий нет!\nВыберите интересующую вас группу:"
        kb.button(text="🔍 Выбрать группу", callback_data="attendance:choose_cohort")

    kb.button(text="⬅️ Назад", callback_data="admin:back")
    kb.adjust(1)

    await message.answer(text, reply_markup=kb.as_markup())


# Добавьте обработчик НА УРОВНЕ МОДУЛЯ, а не внутри функции
@router.callback_query(F.data == "attendance:back_main")
async def back_to_attendance_main(cq: CallbackQuery):
    """Возврат в главное меню посещаемости"""
    print("⬅️ Возвращаемся в главное меню посещаемости...")
    await cq.answer()
    await show_attendance_main(cq.message)


async def show_date_selection(message: Message, cohort_id: str, cohort_name: str):
    """Показывает выбор даты для когорты"""
    print(f"📅 show_date_selection: cohort_id={cohort_id}, cohort_name={cohort_name}")
    today = date.today().isoformat()

    try:
        # Получаем прошедшие даты занятий (включая сегодня)
        print(f"📅 Ищем даты занятий для когорты {cohort_id}...")
        dates = await db.fetch_all("""
                                   SELECT DISTINCT date
                                   FROM session_days
                                   WHERE cohort_id = ? AND date <= ?
                                   ORDER BY date DESC
                                       LIMIT 10
                                   """, (cohort_id, today))

        print(f"📅 Найдено дат: {len(dates)}")

        kb = InlineKeyboardBuilder()

        for date_record in dates:
            date_str = date_record['date']
            display_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m.%Y')
            print(f"➕ Добавляем кнопку даты: {display_date} ({date_str})")
            kb.button(text=display_date, callback_data=f"attendance:cohort:{cohort_id}:{date_str}")

        kb.button(text="⬅️ Назад к группам", callback_data="attendance:choose_cohort")
        kb.adjust(2)

        print("📤 Отправляем меню выбора даты...")
        await message.edit_text(
            f"📅 Выберите дату занятия для группы {cohort_name}:",
            reply_markup=kb.as_markup()
        )
        print("✅ Меню выбора даты отправлено успешно!")

    except Exception as e:
        print(f"💥 Ошибка в show_date_selection: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Ошибка при загрузке дат занятий")


async def show_attendance_marking(message: Message, cohort_id: str, cohort_name: str, session_date: str):
    """Показывает интерфейс для отметки посещения"""
    print(f"📝 show_attendance_marking: cohort_id={cohort_id}, cohort_name={cohort_name}, session_date={session_date}")

    try:
        # Получаем session_id
        session = await db.fetch_one(
            "SELECT id FROM session_days WHERE cohort_id = ? AND date = ?",
            (cohort_id, session_date)
        )

        if not session:
            print("❌ Занятие не найдено в session_days")
            await message.answer("❌ Занятие не найдено")
            return

        session_id = session['id']
        print(f"📝 Найдено занятие с id={session_id}")

        # Получаем студентов когорты
        students = await db.fetch_all("""
                                      SELECT u.id, u.full_name, u.username, u.telegram_id
                                      FROM users u
                                               JOIN participants p ON u.id = p.user_id
                                      WHERE p.cohort_id = ?
                                      ORDER BY u.full_name
                                      """, (cohort_id,))

        if not students:
            print("❌ В этой группе нет студентов")
            await message.answer("❌ В этой группе нет студентов")
            return

        print(f"👥 Найдено студентов: {len(students)}")

        # Получаем текущие статусы посещения
        attendance_data = await db.fetch_all("""
                                             SELECT user_id, status
                                             FROM attendance
                                             WHERE session_id = ?
                                             """, (session_id,))

        attendance_dict = {str(item['user_id']): item['status'] for item in attendance_data}
        print(f"📊 Найдено записей посещаемости: {len(attendance_data)}")

        # Создаем клавиатуру для отметки посещения
        kb = InlineKeyboardBuilder()

        for student in students:
            student_id = str(student['id'])
            current_status = attendance_dict.get(student_id, 'not_set')
            status_text = ATTENDANCE_STATUSES.get(current_status, '⚪ Не отмечен')

            # Кнопка студента с текущим статусом
            kb.button(
                text=f"{student['full_name']} - {status_text}",
                callback_data=f"attendance:student:{cohort_id}:{session_date}:{student_id}"
            )

        # Кнопки управления
        kb.button(text="💾 Сохранить и выйти", callback_data="attendance:save_exit")
        kb.button(text="⬅️ Назад к датам", callback_data=f"attendance:cohort:{cohort_id}")
        kb.adjust(1)

        display_date = datetime.strptime(session_date, '%Y-%m-%d').strftime('%d.%m.%Y')
        await message.edit_text(
            f"📝 Отметка посещения для группы {cohort_name}\n"
            f"📅 Дата: {display_date}\n\n"
            f"Нажмите на студента для изменения статуса:",
            reply_markup=kb.as_markup()
        )
        print("✅ Интерфейс отметки посещения отправлен успешно!")

    except Exception as e:
        print(f"💥 Ошибка в show_attendance_marking: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Ошибка при загрузке интерфейса отметки посещения")


# ДОБАВЬТЕ ЭТОТ ОБРАБОТЧИК ДЛЯ КНОПКИ ИЗ АДМИН-ПАНЕЛИ
@router.callback_query(F.data == "admin:attendance")
async def admin_attendance_handler(cq: CallbackQuery):
    """Обработчик кнопки 'Посещаемость' в админ-панели"""
    await admin_attendance_entry(cq)


@router.callback_query(F.data == "attendance:choose_cohort")
async def choose_cohort(cq: CallbackQuery):
    """Показывает список всех когорт для выбора"""
    print(f"🎯 ОБРАБОТЧИК choose_cohort ВЫЗВАН для пользователя {cq.from_user.id}")
    await cq.answer()

    try:
        print("📋 Делаем запрос к базе...")
        cohorts = await db.fetch_all("SELECT id, name FROM cohorts ORDER BY name")
        print(f"📊 Найдено когорт: {len(cohorts)}")

        if not cohorts:
            print("❌ Когорты не найдены!")
            await cq.message.edit_text("❌ В базе данных нет групп.")
            return

        print("🔨 Создаем клавиатуру...")
        kb = InlineKeyboardBuilder()
        for cohort in cohorts:
            print(f"➕ Добавляем кнопку: {cohort['name']} (id: {cohort['id']})")
            kb.button(text=cohort['name'], callback_data=f"attendance:cohort:{cohort['id']}")

        kb.button(text="⬅️ Назад", callback_data="attendance:back_main")
        kb.adjust(1)

        print("📤 Отправляем сообщение...")
        await cq.message.edit_text("👥 Выберите группу:", reply_markup=kb.as_markup())
        print("✅ Сообщение отправлено успешно!")

    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        await cq.message.answer("❌ Критическая ошибка при загрузке списка групп")


@router.callback_query(F.data.startswith("attendance:cohort:"))
async def process_cohort_selection(cq: CallbackQuery):
    """Обрабатывает выбор когорты и показывает даты занятий"""
    print(f"🎯 ОБРАБОТЧИК process_cohort_selection ВЫЗВАН с data: {cq.data}")
    await cq.answer()

    try:
        parts = cq.data.split(":")
        cohort_id = parts[2]
        selected_date = parts[3] if len(parts) > 3 else None
        print(f"📌 Разобраны части: cohort_id={cohort_id}, selected_date={selected_date}")

        # Получаем информацию о когорте
        print(f"📋 Ищем когорту с id={cohort_id} в базе...")
        cohort = await db.fetch_one("SELECT name FROM cohorts WHERE id = ?", (cohort_id,))
        if not cohort:
            print("❌ Когорта не найдена в базе")
            await cq.message.answer("❌ Группа не найдена")
            return

        print(f"📋 Найдена когорта: {cohort['name']}")

        # Если дата не указана, показываем выбор даты
        if not selected_date:
            print("📅 Дата не указана, вызываем show_date_selection")
            await show_date_selection(cq.message, cohort_id, cohort['name'])
            return

        # Если дата указана, сразу переходим к отметке посещения
        print(f"📅 Дата указана: {selected_date}, вызываем show_attendance_marking")
        await show_attendance_marking(cq.message, cohort_id, cohort['name'], selected_date)

    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА в process_cohort_selection: {e}")
        import traceback
        traceback.print_exc()
        await cq.message.answer("❌ Ошибка при обработке выбора группы")


@router.callback_query(F.data.startswith("attendance:student:"))
async def process_student_attendance(cq: CallbackQuery):
    """Обрабатывает выбор студента для изменения статуса посещения"""
    print(f"🎯 ОБРАБОТЧИК process_student_attendance ВЫЗВАН с data: {cq.data}")
    await cq.answer()

    try:
        parts = cq.data.split(":")
        cohort_id = parts[2]
        session_date = parts[3]
        student_id = parts[4]

        # Получаем информацию о студенте
        student = await db.fetch_one(
            "SELECT full_name FROM users WHERE id = ?",
            (student_id,)
        )

        if not student:
            print("❌ Студент не найден")
            await cq.message.answer("❌ Студент не найден")
            return

        # Создаем клавиатуру выбора статуса
        kb = InlineKeyboardBuilder()

        for status_key, status_text in ATTENDANCE_STATUSES.items():
            kb.button(
                text=status_text,
                callback_data=f"attendance:set_status:{cohort_id}:{session_date}:{student_id}:{status_key}"
            )

        kb.button(text="⬅️ Назад", callback_data=f"attendance:cohort:{cohort_id}:{session_date}")
        kb.adjust(1)

        await cq.message.edit_text(
            f"Выберите статус для студента:\n{student['full_name']}",
            reply_markup=kb.as_markup()
        )

    except Exception as e:
        print(f"💥 Ошибка в process_student_attendance: {e}")
        import traceback
        traceback.print_exc()


@router.callback_query(F.data.startswith("attendance:set_status:"))
async def set_attendance_status(cq: CallbackQuery):
    """Устанавливает статус посещения для студента"""
    print(f"🎯 ОБРАБОТЧИК set_attendance_status ВЫЗВАН с data: {cq.data}")
    await cq.answer()

    try:
        parts = cq.data.split(":")
        cohort_id = parts[2]
        session_date = parts[3]
        student_id = parts[4]
        status = parts[5]
        print(f"📌 Разобраны части: cohort_id={cohort_id}, session_date={session_date}, student_id={student_id}, status={status}")

        # Получаем session_id
        session = await db.fetch_one(
            "SELECT id FROM session_days WHERE cohort_id = ? AND date = ?",
            (cohort_id, session_date)
        )

        if not session:
            print("❌ Занятие не найдено")
            await cq.message.answer("❌ Занятие не найдено")
            return

        session_id = session['id']
        print(f"📝 Session ID: {session_id}")

        # Проверяем существующую запись
        existing = await db.fetch_one(
            "SELECT id FROM attendance WHERE user_id = ? AND session_id = ?",
            (student_id, session_id)
        )

        print(f"📊 Существующая запись: {existing}")

        try:
            if status == 'not_set':
                # Если выбран статус "Не отмечен", удаляем запись
                if existing:
                    print("🗑️ Удаляем запись (статус 'Не отмечен')...")
                    await db.execute(
                        "DELETE FROM attendance WHERE user_id = ? AND session_id = ?",
                        (student_id, session_id)
                    )
            else:
                if existing:
                    # Обновляем существующую запись
                    print("🔄 Обновляем существующую запись...")
                    await db.execute(
                        "UPDATE attendance SET status = ? WHERE user_id = ? AND session_id = ?",
                        (status, student_id, session_id)
                    )
                else:
                    # Создаем новую запись
                    print("➕ Создаем новую запись...")
                    await db.execute(
                        "INSERT INTO attendance (user_id, session_id, status) VALUES (?, ?, ?)",
                        (student_id, session_id, status)
                    )

            # Показываем уведомление об успехе
            status_text = ATTENDANCE_STATUSES.get(status, status)
            student = await db.fetch_one("SELECT full_name FROM users WHERE id = ?", (student_id,))
            if student:
                await cq.answer(f"✅ {student['full_name']} - {status_text}")

            # Возвращаемся к списку студентов
            print("🔄 Возвращаемся к списку студентов...")
            await show_attendance_marking(cq.message, cohort_id, "", session_date)

        except Exception as db_error:
            print(f"💥 Ошибка базы данных: {db_error}")
            await cq.answer("❌ Ошибка базы данных при сохранении")

    except Exception as e:
        print(f"💥 Ошибка в set_attendance_status: {e}")
        import traceback
        traceback.print_exc()
        await cq.answer("❌ Ошибка при сохранении")


@router.callback_query(F.data == "attendance:test_simple")
async def test_simple(cq: CallbackQuery):
    """Простейший тестовый обработчик"""
    print("🎯 ТЕСТОВЫЙ ОБРАБОТЧИК ВЫЗВАН!")
    await cq.answer("Тест работает!")
    await cq.message.edit_text("✅ Тестовое сообщение - обработчик работает!")

# Добавьте остальные обработчики из вашего исходного файла здесь...