
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from .core import get_db_connection

log = logging.getLogger(__name__)

# --------- utils ---------

_COL_SYNONYMS = {
    "date": ["date", "day", "дата", "day_date", "session_day"],
    "code": ["topic_code", "code", "код", "тема_код", "код_темы"],
    "title": ["title", "name", "тема", "тема_название"],
    "annotation": ["annotation", "ann", "описание", "краткое_описание", "desc", "description"],
    "stream": ["stream_id", "cohort_id", "cohort", "поток", "группа"],
}

def _norm(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_а-яА-Я\-]+", "_", s.strip().lower())

def _pick(mapping: Dict[str, int], names: List[str]) -> Optional[int]:
    for n in names:
        if n in mapping:
            return mapping[n]
    return None

def _detect_stream_from_filename(path: Path) -> Optional[int]:
    m = re.search(r"(\\d+)\\s*_cohort", path.stem)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None

# --------- reader ---------

@dataclass
class Row:
    date: str
    code: Optional[str]
    title: Optional[str]
    annotation: Optional[str]
    stream_id: Optional[int]

def _iter_xlsx(path: Path, default_stream: Optional[int]) -> Iterator[Row]:
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        log.error("Pandas is required to read %s (install pandas+openpyxl). Error: %s", path.name, e)
        return

    try:
        df = pd.read_excel(path)  # requires openpyxl
    except Exception as e:
        log.error("Failed to read %s: %s", path, e)
        return

    # Build column map
    cols = { _norm(c): i for i, c in enumerate(df.columns.astype(str).tolist()) }

    idx_date = _pick(cols, _COL_SYNONYMS["date"])
    if idx_date is None:
        log.error("Skip %s: no date column", path.name)
        return

    idx_code = _pick(cols, _COL_SYNONYMS["code"])
    idx_title = _pick(cols, _COL_SYNONYMS["title"])
    idx_ann = _pick(cols, _COL_SYNONYMS["annotation"])
    idx_stream = _pick(cols, _COL_SYNONYMS["stream"])

    for _, row in df.iterrows():
        raw_date = row.iloc[idx_date]
        if pd.isna(raw_date):
            continue
        # Robust date parsing
        d = pd.to_datetime(raw_date, errors="coerce")
        if pd.isna(d):
            # try Excel serial
            try:
                d = pd.to_datetime(float(raw_date), unit="D", origin="1899-12-30")
            except Exception:
                continue
        date_str = d.strftime("%Y-%m-%d")

        def _cell(idx):
            if idx is None:
                return None
            v = row.iloc[idx]
            return None if pd.isna(v) else str(v).strip()

        code = _cell(idx_code)
        title = _cell(idx_title)
        ann = _cell(idx_ann)

        stream_id = None
        sv = _cell(idx_stream)
        if sv is not None:
            try:
                stream_id = int(float(sv))
            except Exception:
                stream_id = default_stream
        else:
            stream_id = default_stream

        yield Row(date=date_str, code=code, title=title, annotation=ann, stream_id=stream_id)

# --------- sync into DB ---------

def sync_schedule_from_files(files: Iterable[str]) -> int:
    """
    Читает XLSX-файлы с расписанием и синхронизирует таблицы:
      - topics (по code) — обновляет title/annotation только реальными данными из файла;
      - session_days (date, stream_id, topic_id, topic_code).
    Возвращает число записей session_days, добавленных/обновлённых.
    """
    added = 0
    with get_db_connection() as con:
        con.row_factory = None
        cur = con.cursor()
        for f in files:
            p = Path(f)
            default_stream = _detect_stream_from_filename(p)
            for r in _iter_xlsx(p, default_stream):
                # topics
                topic_id = None
                if r.code:
                    cur.execute("INSERT OR IGNORE INTO topics(code) VALUES (?)", (r.code,))
                    if r.title is not None:
                        cur.execute("UPDATE topics SET title=? WHERE code=?", (r.title, r.code))
                    if r.annotation is not None:
                        cur.execute("UPDATE topics SET annotation=? WHERE code=?", (r.annotation, r.code))
                    row = cur.execute("SELECT id FROM topics WHERE code=?", (r.code,)).fetchone()
                    topic_id = int(row[0]) if row else None

                # session_days
                cur.execute(
                    """
                    INSERT INTO session_days(date, stream_id, topic_id, topic_code)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(date, stream_id) DO UPDATE SET
                        topic_id=COALESCE(excluded.topic_id, session_days.topic_id),
                        topic_code=COALESCE(excluded.topic_code, session_days.topic_code)
                    """,
                    (r.date, r.stream_id, topic_id, r.code),
                )
                if cur.rowcount is not None and cur.rowcount > 0:
                    added += cur.rowcount
        con.commit()
    log.info("[SYNC] schedule from files done; affected rows=%s", added)
    return added
