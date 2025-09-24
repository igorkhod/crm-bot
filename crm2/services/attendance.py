# crm2/services/attendance.py
from crm2.db import db

async def mark_attendance(user_id: int, session_id: int, status: str, noted_by: int):
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
    sql = "SELECT user_id FROM attendance WHERE session_id=? AND status='present'"
    rows = await db.fetch_all(sql, (session_id,))
    return [row[0] for row in rows]
