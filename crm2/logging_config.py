# === Автогенерированный заголовок: crm2/logging_config.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: setup_logging
# === Конец автозаголовка
#
# === Файл: crm2/logging_config.py
# Аннотация: модуль CRM, настройки/конфигурация, логирование. Внутри функции: setup_logging.
# Добавлено автоматически 2025-08-21 05:43:17

import logging

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )