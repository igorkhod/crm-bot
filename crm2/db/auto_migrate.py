
from __future__ import annotations

import logging
import sqlite3
from typing import Iterable, Optional

from .core import get_db_connection

log = logging.getLogger(__name__)


def ensure_schedule_schema(
    seed_stream_id: int = 2,
    seed_dates: Optional[Iterable[str]] = None,
    seed_topic_code: str = "ПТГ-2",
    seed_title: str = "Психотехнологии гармонии — Сессия 2",
    seed_annotation: str = "Двухдневная сессия (суббота–воскресенье).",
) -> None:
    """
    Idempotent: создаёт таблицы topics/session_days, если их нет.
    Если будущих записей нет, добавляет пару ближайших дат для stream_id.
    """
    if seed_dates is None:
        seed_dates = ("2025-09-13", "2025-09-14")

    with get_db_connection() as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # 1) Таблицы
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                title TEXT,
                annotation TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS session_days (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,        -- YYYY-MM-DD
                stream_id INTEGER,
                topic_id INTEGER,
                topic_code TEXT,
                UNIQUE(date, stream_id)
            )
            """
        )
        con.commit()

        # 2) Если нет будущих записей — посеем минимальный набор
        future_count = cur.execute(
            "SELECT COUNT(*) AS c FROM session_days WHERE date(date) >= date('now')"
        ).fetchone()["c"]

        if future_count == 0:
            # ensure topic
            cur.execute(
                "INSERT OR IGNORE INTO topics(code, title, annotation) VALUES (?, ?, ?)",
                (seed_topic_code, seed_title, seed_annotation),
            )
            topic = cur.execute(
                "SELECT id, code FROM topics WHERE code=? LIMIT 1",
                (seed_topic_code,),
            ).fetchone()
            topic_id = int(topic["id"]) if topic else None

            for d in seed_dates:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO session_days(date, stream_id, topic_id, topic_code)
                    VALUES (?, ?, ?, ?)
                    """,
                    (d, seed_stream_id, topic_id, seed_topic_code),
                )

            con.commit()
            log.warning(
                "[AUTO-MIGRATE] Seeded session_days for stream #%s on dates: %s",
                seed_stream_id,
                ", ".join(seed_dates),
            )
        else:
            log.info("[AUTO-MIGRATE] session_days has %s upcoming record(s), seeding skipped.", future_count)


def apply_topic_overrides(overrides: dict[str, dict[str, str]]) -> None:
    """
    Точечно правит title/annotation по коду темы.
    Идемпотентно: можно вызывать при каждом старте.
    """
    from .core import get_db_connection
    with get_db_connection() as con:
        cur = con.cursor()
        for code, fields in overrides.items():
            if "title" in fields:
                cur.execute("UPDATE topics SET title=? WHERE code=?", (fields["title"], code))
            if "annotation" in fields:
                cur.execute("UPDATE topics SET annotation=? WHERE code=?", (fields["annotation"], code))
        con.commit()
