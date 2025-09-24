# crm2/services/attendance.py
from crm2.db import db


async def mark_attendance(user_id: int, session_id: int, status: str, noted_by: int):
    """
    Отметить посещаемость (UPSERT).
    status: 'present' | 'absent' | 'late'
    """
    sql = """
    INSERT INTO attendance (user_id, session_id, status, noted_by)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, session_id)
    DO UPDATE SET status=excluded.status,
                  noted_at=CURRENT_TIMESTAMP,
                  noted_by=excluded.noted_by
    """
    await db.execute(sql, (user_id, session_id, status, noted_by))


async def get_present_users(session_id: int) -> list[int]:
    """Вернуть ID пользователей, которые присутствовали на занятии."""
    sql = "SELECT user_id FROM attendance WHERE session_id=? AND status='present'"
    rows = await db.fetch_all(sql, (session_id,))
    return [row[0] for row in rows]


async def find_user_id_by_nickname(nick_or_at: str) -> int | None:
    """Найти user_id по nickname (с @ или без)."""
    nick = nick_or_at.lstrip("@")
    sql = "SELECT id FROM users WHERE nickname=?"
    row = await db.fetch_one(sql, (nick,))
    return row[0] if row else None


async def get_sessions_near(days: int = 14):
    """
    Получить список ближайших занятий из session_days (по умолчанию 2 недели).
    """
    sql = """
    SELECT id, date, stream_id, topic_code
    FROM session_days
    WHERE date BETWEEN DATE('now') AND DATE('now', ?)
    ORDER BY date
    """
    return await db.fetch_all(sql, (f"+{days} day",))


# --- Домашние задания ---

async def ensure_homework_delivery_table():
    """Создать таблицу homework_delivery, если её ещё нет."""
    sql = """
    CREATE TABLE IF NOT EXISTS homework_delivery (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        link TEXT NOT NULL,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(session_id, user_id)
    )
    """
    await db.execute(sql)


async def get_not_yet_delivered(session_id: int) -> list[int]:
    """Список user_id, кто был 'present', но ещё не получал ДЗ."""
    await ensure_homework_delivery_table()
    sql = """
    SELECT a.user_id
    FROM attendance a
    WHERE a.session_id=? AND a.status='present'
      AND NOT EXISTS (
          SELECT 1 FROM homework_delivery h
          WHERE h.session_id=a.session_id AND h.user_id=a.user_id
      )
    """
    rows = await db.fetch_all(sql, (session_id,))
    return [row[0] for row in rows]


async def mark_homework_delivered(session_id: int, user_id: int, link: str):
    """Отметить, что курсант получил ДЗ (идемпотентно)."""
    await ensure_homework_delivery_table()
    sql = """
    INSERT OR IGNORE INTO homework_delivery (session_id, user_id, link)
    VALUES (?, ?, ?)
    """
    await db.execute(sql, (session_id, user_id, link))
