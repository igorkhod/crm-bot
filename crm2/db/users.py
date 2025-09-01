"""
crm2/db/users.py
Работа с таблицей users: получение, поиск, создание, обновление.
"""

import sqlite3
from typing import Optional, List, Dict, Any

from crm2.utils.config import DB_PATH


# ───────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ
# ───────────────────────────────────────────────────────────────────────────────

def get_db_connection() -> sqlite3.Connection:
    """
    Открывает соединение с SQLite с row_factory=sqlite3.Row.
    """
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Преобразует sqlite3.Row в dict.
    """
    return dict(row)


# ───────────────────────────────────────────────────────────────────────────────
# ФУНКЦИИ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
# ───────────────────────────────────────────────────────────────────────────────

def list_users() -> List[Dict[str, Any]]:
    """Возвращает список всех пользователей."""
    with get_db_connection() as con:
        rows = con.execute("SELECT * FROM users").fetchall()
        return [_row_to_dict(r) for r in rows]


def list_users_by_role(role: str) -> List[Dict[str, Any]]:
    """Возвращает список пользователей по роли."""
    with get_db_connection() as con:
        rows = con.execute("SELECT * FROM users WHERE role = ?", (role,)).fetchall()
        return [_row_to_dict(r) for r in rows]


def list_users_by_cohort(cohort_id: int) -> List[Dict[str, Any]]:
    """Возвращает список пользователей по cohort_id."""
    with get_db_connection() as con:
        rows = con.execute("SELECT * FROM users WHERE cohort_id = ?", (cohort_id,)).fetchall()
        return [_row_to_dict(r) for r in rows]


def get_user_by_tg(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает пользователя по telegram_id."""
    with get_db_connection() as con:
        row = con.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        return _row_to_dict(row) if row else None


def get_user_by_nickname(nickname: str) -> Optional[Dict[str, Any]]:
    """Возвращает пользователя по nickname."""
    with get_db_connection() as con:
        row = con.execute("SELECT * FROM users WHERE nickname = ?", (nickname,)).fetchone()
        return _row_to_dict(row) if row else None


def delete_user_by_tg(telegram_id: int) -> None:
    """Удаляет пользователя по telegram_id."""
    with get_db_connection() as con:
        con.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        con.commit()


# ───────────────────────────────────────────────────────────────────────────────
# UPSERT (создать или обновить пользователя)
# ───────────────────────────────────────────────────────────────────────────────

def upsert_user(
    telegram_id: int,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    role: Optional[str] = None,
    cohort_id: Optional[int] = None,
    nickname: Optional[str] = None,
    password: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
) -> int:
    """
    Создаёт пользователя, если его нет; иначе — обновляет непустые поля.
    Возвращает id пользователя.
    """
    with get_db_connection() as con:
        cur = con.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()

        if row:
            # обновляем только явно переданные поля
            sets, params = [], []

            def add(col, val):
                if val is not None:
                    sets.append(f"{col} = ?")
                    params.append(val)

            add("username", username)
            add("full_name", full_name)
            add("role", role)
            add("cohort_id", cohort_id)
            add("nickname", nickname)
            add("password", password)
            add("phone", phone)
            add("email", email)

            if sets:
                params.append(telegram_id)
                con.execute(f"UPDATE users SET {', '.join(sets)} WHERE telegram_id = ?", params)
                con.commit()

            return row[0]

        # вставка нового пользователя
        con.execute(
            """
            INSERT INTO users (telegram_id, username, full_name, role, cohort_id, nickname, password, phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                username,
                full_name,
                role or "user",
                cohort_id,
                nickname,
                password,
                phone,
                email,
            ),
        )
        con.commit()
        new_id = con.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()[0]
        return new_id
