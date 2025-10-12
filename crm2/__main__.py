# === Автогенерированный заголовок: crm2/__main__.py ===
# Назначение: точка входа проекта/бота, модуль CRM, асинхронные задачи.
# Классы: —
# Функции: —
# === Конец автозаголовка ===
import asyncio
from .app import main
from .db.auto_migrate import ensure_all_schemas as ensure_min_schema
ensure_min_schema()


if __name__ == "__main__":
    asyncio.run(main())