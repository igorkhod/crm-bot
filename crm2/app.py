# crm2/app.py
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress

from fastapi import FastAPI
from crm2.bot import bot, dp  # ✅ берём готовые экземпляры

app = FastAPI(title="crm2")


@app.get("/health")
async def health():
    return {"ok": True}


def _try_include(module_path: str, attr: str = "router"):
    """Пытаемся подключить роутер модуля, пишем в лог результат."""
    try:
        mod = __import__(module_path, fromlist=[attr])
        r = getattr(mod, attr)
        dp.include_router(r)
        logging.getLogger().info("[ROUTER:ok] %s.%s included", module_path, attr)
    except ModuleNotFoundError:
        logging.getLogger().info("[ROUTER:skip] %s (module not found)", module_path)
    except Exception as e:
        logging.getLogger().exception("[ROUTER:fail] %s: %s", module_path, e)


async def _runner():
    # ---- здесь перечисляем все хэндлеры ----
    _try_include("crm2.handlers.admin.panel")        # ✅ админ-панель (если файл: crm2/handlers/admin/panel.py)
    _try_include("crm2.handlers.admin_attendance")   # ✅ посещаемость + ДЗ
    # Админ: посещаемость и домашние задания
    _try_include("crm2.handlers.admin_attendance")
    _try_include("crm2.handlers.admin_homework")  # если создашь отдельный модуль
    # _try_include("crm2.handlers.admin_homework")   # если вынесешь ДЗ в отдельный модуль

    # Остальные твои хэндлеры:
    _try_include("crm2.handlers.admin_users")
    _try_include("crm2.handlers.admin_db")
    _try_include("crm2.handlers_schedule")
    _try_include("crm2.handlers.about")
    _try_include("crm2.handlers.auth")
    _try_include("crm2.handlers.consent")
    _try_include("crm2.handlers.help")
    _try_include("crm2.handlers.info")
    _try_include("crm2.handlers.profile")
    _try_include("crm2.handlers.registration")
    _try_include("crm2.handlers.start")
    _try_include("crm2.handlers.welcome")

    logging.getLogger().warning("[BUILD] starting application")
    await dp.start_polling(bot)


def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    with suppress(KeyboardInterrupt):
        asyncio.run(_runner())


if __name__ == "__main__":
    main()
