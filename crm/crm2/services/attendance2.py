# crm2/services/attendance.py
"""
Сервисный слой для работы с посещаемостью и рассылкой домашних заданий.
Используется модулем admin_homework.py
"""
import sqlite3
from datetime import date, timedelta
from typing import List, Tuple, Optional

from crm2.db.core import get_db_connection


async def get_sessions_near(days: int = 14) -> List[Tuple[int, str, Optional[int], Optional[str]]]:
    """
    Получить занятия за последние N дней.

    Returns:
        List[(session_id, date_str, stream_id, topic_code)]
    """
    today = date.today()
    start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    with get_db_connection() as con:
        cur = con.execute(
            """
            SELECT id, date, stream_id, topic_code
            FROM session_days
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
            """,
            (start_date, end_date),
        )
        return cur.fetchall()


async def get_present_users(session_id: int) -> List[int]:
    """
    Получить список telegram_id пользователей, отмеченных как 'present' на занятии.

    Args:
        session_id: ID занятия из session_days

    Returns:
        List[telegram_id]
    """
    with get_db_connection() as con:
        cur = con.execute(
            """
            SELECT u.telegram_id
            FROM attendance a
                     JOIN users u ON u.id = a.user_id
            WHERE a.session_id = ?
              AND a.status = 'present'
            """,
            (session_id,),
        )
        return [row[0] for row in cur.fetchall() if row[0]]


async def get_not_yet_delivered(session_id: int) -> Optional[List[int]]:
    """
    Получить telegram_id тех, кто был 'present', но ещё не получил ДЗ.

    Args:
        session_id: ID занятия

    Returns:
        List[telegram_id] или None если занятие не найдено
    """
    # Проверяем существование занятия
    with get_db_connection() as con:
        exists = con.execute(
            "SELECT 1 FROM session_days WHERE id = ? LIMIT 1",
            (session_id,)
        ).fetchone()

        if not exists:
            return None

        # Присутствовавшие
        present_ids = await get_present_users(session_id)
        if not present_ids:
            return []

        # Уже получившие ДЗ
        cur = con.execute(
            """
            SELECT u.telegram_id
            FROM homework_delivery hd
                     JOIN users u ON u.id = hd.user_id
            WHERE hd.session_id = ?
            """,
            (session_id,),
        )
        already_delivered = {row[0] for row in cur.fetchall() if row[0]}

        # Разница
        return [tid for tid in present_ids if tid not in already_delivered]


async def mark_homework_delivered(session_id: int, telegram_id: int, link: str) -> None:
    """
    Отметить, что пользователю отправлено ДЗ.

    Args:
        session_id: ID занятия
        telegram_id: telegram_id получателя
        link: ссылка на ДЗ
    """
    with get_db_connection() as con:
        # Получаем user_id по telegram_id
        user_row = con.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ).fetchone()

        if not user_row:
            return

        user_id = user_row[0]

        # Записываем доставку
        con.execute(
            """
            INSERT INTO homework_delivery (session_id, user_id, link)
            VALUES (?, ?, ?) ON CONFLICT(session_id, user_id) DO NOTHING
            """,
            (session_id, user_id, link),
        )
        con.commit()