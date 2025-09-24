# crm2/app.py
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress

from fastapi import FastAPI

# ✅ импортируем готовые экземпляры
from crm2.bot import bot, dp

# Подключение роутеров (что найдём — то включим, остальное пропустим)
def _try_include(router_path: str, attr: str = "router"):
    try:
        mod = __import__(router_path, fromlist=[attr])
        r = getattr(mod, attr)
        dp.include_router(r)
        logging.getLogger().info("[ROUTER:ok] %s.%s included", router_path, attr)
    except ModuleNotFoundError:
        logging.getLogger().info("[ROUTER:skip] %s (module not found)", router_path)
    except Exception as e:
        logging.getLogger().exception("[ROUTER:fail] %s: %s", router_path, e)

# --- FastAPI приложение (если ты его используешь для healthcheck и пр.)
app = FastAPI(title="crm2")

@app.get("/health")
async def health():
    return {"ok": True}

# --- Точка входа для systemd/cli: python -m crm2
async def _runner():
    # Подключаем все нужные обработчики
    _try_include("crm2.handlers.admin_users")
    _try_include("crm2.handlers.admin_db")
    _try_include("crm2.handlers_schedule")
    _try_include("crm2.handlers.admin.panel")         # твоя админ-панель
    _try_include("crm2.handlers.admin_attendance")    # ✅ посещаемость + ДЗ
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
