from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from typing import Any, Optional

# crm2/services/users.py
# Назначение: Сервис для работы с пользователями - CRUD операции и управление профилями
# Функции:
# - _resolve_db_path - Определение пути к БД через переменные окружения
# - _connect - Создание подключения к БД с настройками
# - get_user_by_telegram - Получение пользователя по Telegram ID
# - get_user_cohort_id_by_tg - Получение ID потока пользователя
# - set_plain_user_field_by_tg - Безопасное обновление полей пользователя
# - upsert_participant_by_tg_sync - Синхронное обновление привязки к потоку
# - upsert_participant_by_tg - Асинхронная обертка для обновления потока
# ───────────────────────── DB path resolver ─────────────────────────
# crm2/services/users.py (добавьте эту функцию)
# crm2/services/users.py
# новое описание:.............................................................../
# crm2/services/users.py
# Назначение: Сервис для работы с пользователями - CRUD операции и управление профилями
# Функции:
# - _resolve_db_path - Определение пути к БД через переменные окружения
# - _connect - Создание подключения к БД с настройками
# - get_user_by_telegram - Получение пользователя по Telegram ID
# - get_user_cohort_id_by_tg - Получение ID потока пользователя
# - set_plain_user_field_by_tg - Безопасное обновление полей пользователя
# - upsert_participant_by_tg_sync - Синхронное обновление привязки к потоку
# - upsert_participant_by_tg - Асинхронная обертка для обновления потока
# - update_user_password - Обновление пароля пользователя
# - set_user_cohort - Установка потока для пользователя
# - get_cohorts - Получение списка всех потоков

logger = logging.getLogger(__name__)


# В services/users.py добавляем функцию:

async def get_user_by_nickname(nickname: str) -> dict | None:
    """Получить пользователя по nickname"""
    query = "SELECT * FROM users WHERE nickname = ?"
    result = await execute_query(query, (nickname,))
    return result[0] if result else None

async def update_user_password(telegram_id: int, new_hashed_password: str) -> bool:
    """Обновляет пароль пользователя в базе данных."""
    try:
        def sync_update():
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET password = ? WHERE telegram_id = ?",
                    (new_hashed_password, telegram_id)
                )
                conn.commit()
                return cursor.rowcount > 0

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_update)
        return result
    except Exception as e:
        logging.error(f"Error updating password for user {telegram_id}: {e}")
        return False


async def update_user_password(telegram_id: int, new_hashed_password: str) -> None:
    """Обновляет пароль пользователя по telegram_id."""

    def sync_update():
        with _connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password = ? WHERE telegram_id = ?",
                (new_hashed_password, telegram_id)
            )
            conn.commit()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, sync_update)


# ───────────────────────── DB path resolver ─────────────────────────
def _resolve_db_path() -> str:
    """
    Порядок:
      1) DB_PATH из .env/.env.local
      2) CRM_DB из .env/.env.local
      3) локальный путь crm2/data/crm.db
    """
    candidates = [
        os.getenv("DB_PATH"),
        os.getenv("CRM_DB"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "crm.db"),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    # последний шанс — всё равно возвращаем локальный дефолт
    return candidates[-1]


DB_PATH = _resolve_db_path()


def _connect() -> sqlite3.Connection:
    """Создание подключения к БД"""
    # Создаем директорию если не существует
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    # немного ускорим запись при наших объёмах
    con.execute("PRAGMA journal_mode=WAL;")
    return con


# ───────────────────────── Публичные функции ─────────────────────────
async def get_user_by_telegram(telegram_id: int) -> dict | None:
    """
    Получаем пользователя по Telegram ID (асинхронная версия)
    """
    try:
        def sync_get_user():
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, telegram_id, nickname, full_name, role, phone, email, cohort_id, password, created_at FROM users WHERE telegram_id = ?",
                    (telegram_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None

        # Запускаем синхронную операцию в отдельном потоке
        loop = asyncio.get_event_loop()
        user = await loop.run_in_executor(None, sync_get_user)
        return user
    except Exception as e:
        logging.error(f"Error getting user by telegram {telegram_id}: {e}")
        return None


# async def set_user_cohort(telegram_id: int, cohort_id: int) -> bool:
async def set_user_cohort(telegram_id: int, cohort_id: int) -> bool:
    """
    Устанавливаем cohort_id для пользователя и синхронизируем с participants
    """
    try:
        def sync_set_cohort():
            with _connect() as conn:
                cursor = conn.cursor()

                # 1. Обновляем cohort_id в users
                cursor.execute(
                    "UPDATE users SET cohort_id = ? WHERE telegram_id = ?",
                    (cohort_id, telegram_id)
                )

                # 2. Получаем user_id для обновления participants
                cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
                user_row = cursor.fetchone()

                if user_row:
                    user_id = user_row['id']

                    # 3. Обновляем или вставляем запись в participants
                    cursor.execute("""
                        INSERT OR REPLACE INTO participants (user_id, cohort_id, created_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """, (user_id, cohort_id))

                conn.commit()
                return cursor.rowcount > 0

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_set_cohort)
        return result
    except Exception as e:
        logging.error(f"Error setting cohort for user {telegram_id}: {e}")
        return False


async def get_cohorts() -> list[dict]:
    """
    Получаем список всех потоков (асинхронная версия)
    """
    try:
        def sync_get_cohorts():
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM cohorts ORDER BY id")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        loop = asyncio.get_event_loop()
        cohorts = await loop.run_in_executor(None, sync_get_cohorts)
        return cohorts
    except Exception as e:
        logging.error(f"Error getting cohorts: {e}")
        return []


# ───────────────────────── Синхронные функции ─────────────────────────
def set_plain_user_field_by_tg(tg_id: int, field: str, value: Any) -> None:
    """
    Обновляет одно из разрешённых полей в таблице users по telegram_id.
    (безопасный белый список)
    """
    allowed = {
        "nickname",
        "password",
        "full_name",
        "phone",
        "email",
        "cohort_id",
        "role",
        "events",
        "participants",
    }
    if field not in allowed:
        raise ValueError(f"Forbidden field: {field}")

    with _connect() as con:
        con.execute(f"UPDATE users SET {field} = ? WHERE telegram_id = ?", (value, int(tg_id)))
        con.commit()


def upsert_participant_by_tg_sync(tg_id: int, cohort_id: Optional[int]) -> None:
    """
    Обновляет таблицу participants так, чтобы была согласованность с users.cohort_id.
    - Если cohort_id is None — удаляем запись участника (сброс потока).
    - Иначе — INSERT ... ON CONFLICT(user_id) DO UPDATE.
    """
    with _connect() as con:
        cur = con.execute("SELECT id FROM users WHERE telegram_id = ? LIMIT 1", (int(tg_id),))
        row = cur.fetchone()
        if not row:
            return
        user_id = int(row["id"])

        if cohort_id is None:
            con.execute("DELETE FROM participants WHERE user_id = ?", (user_id,))
            con.commit()
            return

        con.execute(
            """
            INSERT INTO participants (user_id, cohort_id)
            VALUES (?, ?) ON CONFLICT(user_id) DO
            UPDATE SET cohort_id = excluded.cohort_id
            """,
            (user_id, int(cohort_id)),
        )
        con.commit()


# Неблокирующая «обёртка» — если кто-то вызывает через await
async def upsert_participant_by_tg(tg_id: int, cohort_id: Optional[int]) -> None:
    """Асинхронная обертка для upsert_participant_by_tg_sync"""

    def sync_upsert():
        upsert_participant_by_tg_sync(tg_id, cohort_id)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, sync_upsert)


# ───────────────────────── Дополнительные функции ─────────────────────────
async def get_user_cohort_id_by_tg(telegram_id: int) -> int | None:
    """
    Получаем cohort_id пользователя по Telegram ID
    """
    try:
        user = await get_user_by_telegram(telegram_id)
        return user.get('cohort_id') if user else None
    except Exception as e:
        logging.error(f"Error getting cohort_id for user {telegram_id}: {e}")
        return None


# Добавьте эти функции в конец файла users.py

async def execute_query(query: str, params: tuple = ()) -> list:
    """Выполняет SQL запрос и возвращает результат"""
    try:
        def sync_execute():
            with _connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                conn.commit()
                return []

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_execute)
        return result
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return []

async def update_user_telegram_id(user_id: int, telegram_id: int) -> bool:
    """Обновляет telegram_id для пользователя"""
    try:
        query = "UPDATE users SET telegram_id = ? WHERE id = ?"
        await execute_query(query, (telegram_id, user_id))
        return True
    except Exception as e:
        logging.error(f"Error updating telegram_id: {e}")
        return False

async def get_user_by_nickname(nickname: str) -> dict | None:
    """Получить пользователя по nickname (исправленная версия)"""
    query = "SELECT * FROM users WHERE nickname = ?"
    result = await execute_query(query, (nickname,))
    return result[0] if result else None


async def create_test_user_if_not_exists():
    """Создает тестового пользователя если его нет в базе"""
    try:
        # Проверяем существует ли пользователь
        test_user = await get_user_by_nickname("igor_khod")

        if not test_user:
            logging.info("👤 Создаем тестового пользователя igor_khod...")

            def sync_create():
                with _connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT INTO users
                               (nickname, password, role, full_name, telegram_id)
                           VALUES (?, ?, ?, ?, ?)""",
                        ("igor_khod", "123456", "user", "Игорь Тестовый", None)
                    )
                    conn.commit()

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, sync_create)
            logging.info("✅ Тестовый пользователь создан")
        else:
            logging.info(f"✅ Тестовый пользователь уже существует: {test_user}")

    except Exception as e:
        logging.error(f"❌ Ошибка создания тестового пользователя: {e}")