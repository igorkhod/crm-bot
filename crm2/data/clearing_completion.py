# \crm2\data\clearing_completion.py
# crm2/data/clearing_completion.py
# Назначение: Очистка и перезаполнение таблицы session_days, исправление структуры базы и заполнение расписанием из Excel файлов
# Функции:
# - check_database_state - Проверяет текущее состояние базы данных (когорты, топики, сессии)
# - parse_excel_to_session_days - Парсит Excel файл и добавляет данные в session_days
# - main - Основная функция скрипта: проверка состояния, автоматическое сопоставление файлов и когорт, очистка и заполнение таблицы
"""
Модуль очистки и перезаполнения таблицы session_days
Исправляет структуру базы и заполняет расписанием из Excel файлов
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os


def check_database_state(db_path):
    """Проверяет текущее состояние базы данных"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print("ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ")
    print("=" * 60)

    # Проверяем cohorts
    cursor.execute("SELECT id, name FROM cohorts ORDER BY id")
    cohorts = cursor.fetchall()
    print("\nКОГОРТЫ:")
    for cohort in cohorts:
        print(f"  ID: {cohort[0]}, Name: {cohort[1]}")

    # Проверяем topics
    cursor.execute("SELECT id, code, title FROM topics ORDER BY id")
    topics = cursor.fetchall()
    print("\nТОПИКИ:")
    for topic in topics:
        print(f"  ID: {topic[0]}, Code: {topic[1]}, Title: {topic[2][:50]}...")

    # Проверяем session_days
    cursor.execute("SELECT COUNT(*) FROM session_days")
    session_count = cursor.fetchone()[0]
    print(f"\nДНЕЙ ЗАНЯТИЙ В БАЗЕ: {session_count}")

    if session_count > 0:
        cursor.execute("""
                       SELECT sd.id, sd.date, c.name as cohort_name, t.code as topic_code
                       FROM session_days sd
                                JOIN cohorts c ON sd.cohort_id = c.id
                                JOIN topics t ON sd.topic_id = t.id
                       ORDER BY sd.date LIMIT 5
                       """)
        sample_sessions = cursor.fetchall()
        print("ПЕРВЫЕ 5 ЗАНЯТИЙ:")
        for session in sample_sessions:
            print(f"  ID: {session[0]}, Date: {session[1]}, Cohort: {session[2]}, Topic: {session[3]}")

    conn.close()
    return cohorts, topics


def parse_excel_to_session_days(db_path, excel_file, cohort_id, cohort_name):
    """Парсит Excel файл и добавляет данные в session_days"""

    print(f"\nОБРАБОТКА: {excel_file} для когорты {cohort_name} (ID: {cohort_id})")
    print("-" * 50)

    try:
        # Читаем Excel файл
        df = pd.read_excel(excel_file, sheet_name='Лист1')

        # Нормализуем названия столбцов (убираем пробелы, приводим к нижнему регистру)
        df.columns = [col.strip().lower() for col in df.columns]
        print(f"Нормализованные столбцы: {df.columns.tolist()}")

    except Exception as e:
        print(f"Ошибка при чтении Excel файла: {e}")
        return

    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    added_days = 0
    skipped_rows = 0

    for index, row in df.iterrows():
        # Проверяем наличие необходимых столбцов
        if 'start_date' not in df.columns or 'end_date' not in df.columns or 'topic_code' not in df.columns:
            print("ОШИБКА: В файле отсутствуют необходимые столбцы (start_date, end_date, topic_code)")
            break

        # Пропускаем строки с пустыми датами
        if pd.isna(row['start_date']) or pd.isna(row['end_date']):
            skipped_rows += 1
            continue

        # Получаем topic_id
        topic_code = str(row['topic_code']).strip()
        cursor.execute("SELECT id FROM topics WHERE code = ?", (topic_code,))
        topic_result = cursor.fetchone()

        if not topic_result:
            print(f"  Пропуск: топик '{topic_code}' не найден в базе")
            skipped_rows += 1
            continue

        topic_id = topic_result[0]

        # Создаем записи для каждого дня занятия
        try:
            start_date = pd.to_datetime(row['start_date']).date()
            end_date = pd.to_datetime(row['end_date']).date()

            current_date = start_date
            while current_date <= end_date:
                cursor.execute("""
                               INSERT INTO session_days (date, cohort_id, topic_id, topic_code)
                               VALUES (?, ?, ?, ?)
                               """, (current_date.isoformat(), cohort_id, topic_id, topic_code))

                current_date += timedelta(days=1)
                added_days += 1

        except Exception as e:
            print(f"  Ошибка в строке {index}: {e}")
            skipped_rows += 1
            continue

    conn.commit()
    conn.close()

    print(f"РЕЗУЛЬТАТ:")
    print(f"  Добавлено дней: {added_days}")
    print(f"  Пропущено строк: {skipped_rows}")


def main():
    """Основная функция скрипта"""
    db_path = 'C:\\Users\\user\\PycharmProjects\\crm\\crm2\\data\\crm.db'

    # 1. Проверяем текущее состояние базы
    cohorts, topics = check_database_state(db_path)

    # 2. Автоматически определяем соответствие файлов и когорт
    print("\n" + "=" * 60)
    print("АВТОМАТИЧЕСКОЕ СОПОСТАВЛЕНИЕ ФАЙЛОВ И КОГОРТ")
    print("=" * 60)

    # Создаем когорты на основе имен файлов
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cohort_mapping = {}

    # Для schedule_2025_1_cohort.xlsx используем когорту "2025_1" (уже существует)
    file_1 = 'schedule_2025_1_cohort.xlsx'
    cohort_name_1 = '2025_1'
    cohort_id_1 = None

    # Ищем существующую когорту
    for c_id, c_name in cohorts:
        if c_name == cohort_name_1:
            cohort_id_1 = c_id
            break

    if cohort_id_1:
        print(f"Файл {file_1} → когорта '{cohort_name_1}' (ID: {cohort_id_1})")
        cohort_mapping[file_1] = (cohort_id_1, cohort_name_1)
    else:
        print(f"Когорта '{cohort_name_1}' не найдена!")

    # Для schedule_2025_2_cohort.xlsx создаем когорту "2025_2"
    file_2 = 'schedule_2025_2_cohort.xlsx'
    cohort_name_2 = '2025_2'

    # Создаем новую когорту
    cursor.execute("INSERT INTO cohorts (name) VALUES (?)", (cohort_name_2,))
    cohort_id_2 = cursor.lastrowid
    conn.commit()

    print(f"Файл {file_2} → создана когорта '{cohort_name_2}' (ID: {cohort_id_2})")
    cohort_mapping[file_2] = (cohort_id_2, cohort_name_2)

    conn.close()

    # 3. Очищаем таблицу перед заполнением
    print("\nОчистка таблицы session_days...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session_days")
    conn.commit()
    conn.close()
    print("Таблица session_days очищена")

    # 4. Заполняем данными
    for file, (cohort_id, cohort_name) in cohort_mapping.items():
        full_path = os.path.join(os.path.dirname(db_path), file)
        if os.path.exists(full_path):
            parse_excel_to_session_days(db_path, full_path, cohort_id, cohort_name)
        else:
            print(f"Файл не найден: {full_path}")

    # 5. Финальная проверка
    print("\n" + "=" * 60)
    print("ФИНАЛЬНАЯ ПРОВЕРКА")
    print("=" * 60)
    check_database_state(db_path)


if __name__ == "__main__":
    main()