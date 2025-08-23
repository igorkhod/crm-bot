#
# === Файл: crm2/__main__.py
# Аннотация: точка входа проекта/бота, модуль CRM, асинхронные задачи.
# Добавлено автоматически 2025-08-21 05:43:17

import asyncio
from .app import main
from .db.bootstrap import ensure_min_schema
ensure_min_schema()


if __name__ == "__main__":
    asyncio.run(main())