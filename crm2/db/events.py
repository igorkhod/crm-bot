# crm2/db/events.py
# Назначение: Работа с таблицей events (мероприятия) - подсчет предстоящих событий
# Функции:
# - upcoming_events_count - Возвращает количество будущих мероприятий (дата >= сегодня)

from __future__ import annotations
import sqlite3
from crm2.db.sqlite import DB_PATH

def upcoming_events_count() -> int:
    """Вернёт количество будущих мероприятий (date >= сегодня)."""
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
            SELECT COUNT(*)
            FROM events
            WHERE date(event_date) >= date('now')
        """)
        (cnt,) = cur.fetchone() or (0,)
        return int(cnt or 0)
