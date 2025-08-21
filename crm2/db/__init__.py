# === Файл: crm2/db/__init__.py
# Аннотация: модуль CRM.
# Добавлено автоматически 2025-08-21 05:43:17

from .sqlite import DB_PATH, ensure_schema
__all__ = ["DB_PATH", "ensure_schema"]