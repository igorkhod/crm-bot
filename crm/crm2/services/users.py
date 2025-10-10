# crm2/services/users.py
from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, Optional

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
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    # немного ускорим запись при наших объёмах
    con.execute("PRAGMA journal_mode=WAL;")
    return con


# ───────────────────────── Публичные функции ─────────────────────────
def get_user_by_telegram(tg_id: int) -> Optional[Dict[str, Any]]:
    """
    Вернёт словарь с полями из users по telegram_id или None.
    """
    with _connect() as con:
        cur = con.execute(
            "SELECT * FROM users WHERE telegram_id = ? LIMIT 1",
            (int(tg_id),),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_cohort_id_by_tg(tg_id: int) -> Optional[int]:
    """
    Вернёт cohort_id пользователя по telegram_id.
    """
    with _connect() as con:
        cur = con.execute(
            "SELECT cohort_id FROM users WHERE telegram_id = ? LIMIT 1",
            (int(tg_id),),
        )
        row = cur.fetchone()
        if not row:
            return None
        val = row["cohort_id"]
        return int(val) if val is not None else None


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
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET cohort_id = excluded.cohort_id
            """,
            (user_id, int(cohort_id)),
        )
        con.commit()


# Неблокирующая «обёртка» — если кто-то вызывает через await
async def upsert_participant_by_tg(tg_id: int, cohort_id: Optional[int]) -> None:
    # для простоты выполняем синхронно; при необходимости можно заменить на to_thread
    upsert_participant_by_tg_sync(tg_id, cohort_id)
