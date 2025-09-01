# === Автогенерированный заголовок: crm2/services/users.py
# Список верхнеуровневых объектов файла (классы и функции).
# Обновляется вручную при изменении состава функций/классов.
# Классы: —
# Функции: _now_iso, ensure_user, classify_role, set_role, get_user_by_telegram, verify_password, get_user_cohort_id_by_tg, get_user_cohort_title_by_tg, get_user_cohort_code_by_tg
# === Конец автозаголовка
#
# === Файл: crm2/services/users.py
# Аннотация: модуль CRM, доступ к SQLite/ORM. Внутри функции: _now_iso, ensure_user, classify_role, set_role, get_user_by_telegram.
# Добавлено автоматически 2025-08-21 05:43:17

from datetime import datetime
import sqlite3
import aiosqlite
from crm2.db.sqlite import DB_PATH
from crm2.db.core import get_db_connection
from typing import Dict, Any, Optional

def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


async def ensure_user(tg_id: int, full_name: str | None = None) -> Dict[str, Any]:
    """Создаёт гостя при первом заходе; обновляет last_seen при следующих."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,))
        row = await cur.fetchone()

        if row is None:
            # created_at выставится по DEFAULT, cohort_id по умолчанию NULL
            await db.execute(
                "INSERT INTO users (telegram_id, full_name, role, last_seen) VALUES (?,?,?,?)",
                (tg_id, full_name or "", "curious", _now_iso())
            )
            await db.commit()

            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,))
            row = await cur.fetchone()
        else:
            await db.execute(
                "UPDATE users SET last_seen = ? WHERE telegram_id = ?",
                (_now_iso(), tg_id)
            )
            await db.commit()

    return dict(row)  # type: ignore


async def classify_role(role: str) -> str:
    """Вернёт читабельное название роли"""
    mapping = {
        "curious": "Гость",
        "user": "Курсант",
        "advanced_user": "Продвинутый",
        "admin": "Администратор",
    }
    return mapping.get(role, role)


async def set_role(tg_id: int, role: str) -> None:
    """Обновляет роль пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?",
            (role, tg_id)
        )
        await db.commit()

# --- выборка пользователя по telegram_id -------------------------------------
def get_user_by_telegram(telegram_id: int) -> dict | None:
    """
    Вернёт всю запись пользователя как dict по telegram_id,
    либо None, если такого пользователя нет.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (int(telegram_id),)
        ).fetchone()
    return dict(row) if row else None


# --- проверка логина/пароля ---------------------------------------------------
def verify_password(nickname: str, password: str) -> bool:
    """
    Возвращает True, если в таблице users есть запись с таким nickname и password.
    (Если у тебя пароли хешируются — здесь нужно будет заменить сравнение.)
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT 1 FROM users WHERE nickname = ? AND password = ?",
            (nickname, password),
        ).fetchone()
    return row is not None


# --- поток пользователя по tg_id ---------------------------------------------
def get_user_cohort_id_by_tg(tg_id: int) -> Optional[int]:
    """
    Возвращает cohort_id пользователя по его Telegram ID, если он есть в participants.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT p.cohort_id
            FROM users u
            JOIN participants p ON p.user_id = u.id
            WHERE u.telegram_id = ?
            ORDER BY p.id
            LIMIT 1
            """,
            (tg_id,),
        ).fetchone()
    return int(row["cohort_id"]) if row else None


def get_user_cohort_title_by_tg(tg_id: int) -> Optional[str]:
    """
    Возвращает название потока (cohorts.title) пользователя по его Telegram ID.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT s.title AS cohort_title
            FROM users u
            JOIN participants p ON p.user_id = u.id
            JOIN cohorts      s ON s.id = p.cohort_id
            WHERE u.telegram_id = ?
            ORDER BY p.id
            LIMIT 1
            """,
            (tg_id,),
        ).fetchone()
    return str(row["cohort_title"]) if row else None


# Для обратной совместимости: код потока == title (в твоей схеме нет s.code)
def get_user_cohort_code_by_tg(tg_id: int) -> Optional[str]:
    """
    Совместимость с существующими вызовами.
    Возвращает то же, что и get_user_cohort_title_by_tg.
    """
    return get_user_cohort_title_by_tg(tg_id)
