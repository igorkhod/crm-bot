# === Автогенерированный заголовок: crm2/cli_import_schedule.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: main
# === Конец автозаголовка
# === Файл: crm2/cli_import_schedule.py
# Назначение: одноразовый импорт расписания из XLSX в session_days (вне запуска бота)
# Запуск на сервере (SSH):
# python -m crm2.cli_import_schedule schedule_2025_1_cohort.xlsx schedule_2025_2_cohort.xlsx

import argparse
import logging
from crm2.db.auto_migrate import ensure_schedule_schema
from crm2.db.schedule_loader import sync_schedule_from_files

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Импорт расписания в session_days из XLSX")
    parser.add_argument("files", nargs="+", help="Пути к файлам Excel (schedule_*.xlsx)")
    args = parser.parse_args()

    ensure_schedule_schema()
    affected = sync_schedule_from_files(args.files)
    print(f"[IMPORT] done; affected rows={affected}")

if __name__ == "__main__":
    main()


# === конец Файла: crm2/cli_import_schedule.py
# Запуск на сервере (SSH):
# python -m crm2.cli_import_schedule schedule_2025_1_cohort.xlsx schedule_2025_2_cohort.xlsx