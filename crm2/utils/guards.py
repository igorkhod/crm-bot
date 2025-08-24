from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from crm2.db.core import get_db_connection

class AdminOnly(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
                       event, data: Dict[str, Any]) -> Any:
        uid = event.from_user.id
        with get_db_connection() as con:
            row = con.execute("SELECT role FROM users WHERE telegram_id=?", (uid,)).fetchone()
        if not row or (row[0] or "user") not in ("admin",):
            # молча игнорим; можешь отправить «нет доступа»
            return
        return await handler(event, data)
