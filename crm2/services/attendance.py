from __future__ import annotations

import sqlite3
from typing import List, Dict, Any
from datetime import date
from typing import Optional

# crm2/services/attendance.py
# Назначение: Сервисный слой для работы с посещаемостью и домашними заданиями (синхронная версия)
# Функции:
# - find_today_session - Поиск сегодняшнего занятия в session_days
# - find_recent_past_sessions - Получение последних прошедших занятий
# - get_stream_title - Получение названия потока
# - get_attendance_map - Получение карты посещаемости для сессии
# - upsert_attendance - Обновление/добавление записи посещаемости
# - status_to_emoji/emoji_to_status - Конвертация статусов в эмодзи и обратно
# - mark_attendance - Асинхронное отметка посещаемости
# - get_present_users - Получение присутствовавших пользователей
# - find_user_id_by_nickname - Поиск user_id по никнейму
# - get_sessions_near - Получение ближайших сессий
# - ensure_homework_delivery_table - Создание таблицы доставки ДЗ
# - get_not_yet_delivered - Получение пользователей без доставленных ДЗ
# - mark_homework_delivered - Отметка доставки ДЗ
# новое описание:
# crm2/services/attendance.py
# Назначение: Сервисный слой для работы с посещаемостью и домашними заданиями (синхронная версия)
# Функции:
# - find_today_session - Поиск сегодняшнего занятия в session_days
# - find_recent_past_sessions - Получение последних прошедших занятий
# - get_stream_title - Получение названия потока
# - get_attendance_map - Получение карты посещаемости для сессии
# - upsert_attendance - Обновление/добавление записи посещаемости
# - status_to_emoji/emoji_to_status - Конвертация статусов в эмодзи и обратно
# - mark_attendance - Асинхронное отметка посещаемости
# - get_present_users - Получение присутствовавших пользователей
# - find_user_id_by_nickname - Поиск user_id по никнейму
# - get_sessions_near - Получение ближайших сессий
# - ensure_homework_delivery_table - Создание таблицы доставки ДЗ
# - get_not_yet_delivered - Получение пользователей без доставленных ДЗ
# - mark_homework_delivered - Отметка доставки ДЗ
from crm2.db.core import get_db_connection, DB_PATH
# crm2/services/attendance.py
from crm2.db import db
from crm2.db.core import get_db_connection

TODAY = date.today().isoformat()


def find_today_session() -> Optional[Dict[str, Any]]:
    """
    Ищем занятие на сегодняшнюю дату в session_days.
    Если несколько (по разным потокам) — берём с максимальным id (последнее заведённое).
    """
    q = """
        SELECT id, date, cohort_id, topic_id, topic_code
        FROM session_days
        WHERE date = ?
        ORDER BY id DESC
            LIMIT 1 \
        """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        row = con.execute(q, (TODAY,)).fetchone()
    return dict(row) if row else None


def find_recent_past_sessions(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Последние прошедшие занятия (date < today), по убыванию даты/id.
    """
    q = """
        SELECT id, date, cohort_id, topic_id, topic_code
        FROM session_days
        WHERE date < ?
        ORDER BY date DESC, id DESC
            LIMIT ? \
        """
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(q, (TODAY, limit)).fetchall()
    return [dict(r) for r in rows]


def get_stream_title(cohort_id: int) -> str:
    """
    streams пуста → подставляем 'Поток N'. Если позже появится title — будем читать из streams.
    """
    # Пробуем прочитать из streams
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT title FROM streams WHERE id = ?", (cohort_id,)).fetchone()
    if row and row["title"]:
        return row["title"]
    return f"Поток {cohort_id}"


def get_attendance_map(session_id: int) -> Dict[int, str]:
    """
    Ключ: user_id → значение status ('present'|'absent'|'left').
    """
    q = "SELECT user_id, status FROM attendance WHERE session_id = ?"
    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(q, (session_id,)).fetchall()
    return {r["user_id"]: r["status"] for r in rows}


def upsert_attendance(user_id: int, session_id: int, status: str, noted_by: Optional[int]) -> None:
    """
    Вставить/обновить отметку. Если запись есть — обновляем status/ts/noted_by.
    """
    with get_db_connection() as con:
        con.execute("""
                    INSERT INTO attendance (user_id, session_id, status, noted_at, noted_by)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?) ON CONFLICT(user_id, session_id) DO
                    UPDATE SET
                        status=excluded.status,
                        noted_at= CURRENT_TIMESTAMP,
                        noted_by=excluded.noted_by
                    """, (user_id, session_id, status, noted_by))
        con.commit()


def status_to_emoji(status: Optional[str]) -> str:
    return {"present": "✅", "absent": "❌", "left": "⛔️"}.get(status or "", "▫️")


def emoji_to_status(emoji: str) -> str:
    return {"✅": "present", "❌": "absent", "⛔️": "left"}.get(emoji, "present")  # по умолчанию present


async def mark_attendance(user_id: int, session_id: int, status: str, noted_by: int):
    """
    Отметить посещаемость (UPSERT).
    status: 'present' | 'absent' | 'late'
    """
    sql = """
          INSERT INTO attendance (user_id, session_id, status, noted_by)
          VALUES (?, ?, ?, ?) ON CONFLICT(user_id, session_id)
    DO
          UPDATE SET status=excluded.status,
              noted_at= CURRENT_TIMESTAMP,
              noted_by=excluded.noted_by \
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
          SELECT id, date, cohort_id, topic_code
          FROM session_days
          WHERE date BETWEEN DATE ('now') AND DATE ('now', ?)
          ORDER BY date \
          """
    return await db.fetch_all(sql, (f"+{days} day",))


# --- Домашние задания ---

async def ensure_homework_delivery_table():
    """Создать таблицу homework_delivery, если её ещё нет."""
    sql = """
          CREATE TABLE IF NOT EXISTS homework_delivery
          (
              id
              INTEGER
              PRIMARY
              KEY,
              session_id
              INTEGER
              NOT
              NULL,
              user_id
              INTEGER
              NOT
              NULL,
              link
              TEXT
              NOT
              NULL,
              sent_at
              TEXT
              DEFAULT
              CURRENT_TIMESTAMP,
              UNIQUE
          (
              session_id,
              user_id
          )
              ) \
          """
    await db.execute(sql)


async def get_not_yet_delivered(session_id: int) -> list[int]:
    """Список user_id, кто был 'present', но ещё не получал ДЗ."""
    await ensure_homework_delivery_table()
    sql = """
          SELECT a.user_id
          FROM attendance a
          WHERE a.session_id = ?
            AND a.status = 'present'
            AND NOT EXISTS (SELECT 1
                            FROM homework_delivery h
                            WHERE h.session_id = a.session_id
                              AND h.user_id = a.user_id) \
          """
    rows = await db.fetch_all(sql, (session_id,))
    return [row[0] for row in rows]


async def mark_homework_delivered(session_id: int, user_id: int, link: str):
    """Отметить, что курсант получил ДЗ (идемпотентно)."""
    await ensure_homework_delivery_table()
    sql = """
          INSERT
          OR IGNORE INTO homework_delivery (session_id, user_id, link)
    VALUES (?, ?, ?) \
          """
    await db.execute(sql, (session_id, user_id, link))
