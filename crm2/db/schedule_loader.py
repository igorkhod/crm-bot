
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from .core import get_db_connection

log = logging.getLogger(__name__)

# --------- utils ---------

_COL_SYNONYMS = {
    "date": ["date", "day", "дата", "day_date", "session_day", "дата_занятия"],
    "start": ["start_date", "start", "начало", "дата_начала"],
    "end": ["end_date", "end", "конец", "дата_окончания", "finish", "finish_date"],
    "code": ["topic_code", "code", "код", "тема_код", "код_темы"],
    "title": ["title", "name", "тема", "тема_название", "название"],
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
    m = re.search(r"(\d+)\s*_cohort", path.stem)
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

    cols_norm_map: Dict[str, int] = { _norm(c): i for i, c in enumerate(df.columns.astype(str).tolist()) }
    log.info("[SCHEDULE] %s columns: %s", path.name, list(cols_norm_map.keys()))

    # pick indices
    idx_date = _pick(cols_norm_map, _COL_SYNONYMS["date"])
    idx_start = _pick(cols_norm_map, _COL_SYNONYMS["start"])
    idx_end = _pick(cols_norm_map, _COL_SYNONYMS["end"])
    idx_code = _pick(cols_norm_map, _COL_SYNONYMS["code"])
    idx_title = _pick(cols_norm_map, _COL_SYNONYMS["title"])
    idx_ann = _pick(cols_norm_map, _COL_SYNONYMS["annotation"])
    idx_stream = _pick(cols_norm_map, _COL_SYNONYMS["stream"])

    # helper
    def _to_date(v):
        d = pd.to_datetime(v, errors="coerce", dayfirst=True)
        return None if pd.isna(d) else d.normalize()

    # iterate rows
    for _, row in df.iterrows():
        # determine date(s)
        dates_list = []

        if idx_start is not None or idx_end is not None:
            v_start = row.iloc[idx_start] if idx_start is not None else None
            v_end = row.iloc[idx_end] if idx_end is not None else None
            d_start = _to_date(v_start) or _to_date(v_end)
            d_end = _to_date(v_end) or _to_date(v_start)
            if d_start is not None:
                if d_end is None or d_end < d_start:
                    d_end = d_start
                cur = d_start
                while cur <= d_end:
                    dates_list.append(cur.strftime("%Y-%m-%d"))
                    cur = cur + timedelta(days=1)
        elif idx_date is not None:
            v = row.iloc[idx_date]
            d = _to_date(v)
            if d is not None:
                dates_list.append(d.strftime("%Y-%m-%d"))
        else:
            # Try auto-detect: find the first column that looks like dates
            try:
                import pandas as pd
                best_idx, best_hits = None, -1
                for i in range(df.shape[1]):
                    series = df.iloc[:, i]
                    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
                    hits = int(parsed.notna().sum())
                    if hits > best_hits:
                        best_idx, best_hits = i, hits
                if best_idx is not None and best_hits >= 3:
                    v = row.iloc[best_idx]
                    d = _to_date(v)
                    if d is not None:
                        dates_list.append(d.strftime("%Y-%m-%d"))
            except Exception:
                pass

        if not dates_list:
            continue

        # extract other fields
        def _cell(idx):
            if idx is None:
                return None
            v = row.iloc[idx]
            return None if (v is None or (hasattr(v, "isna") and v.isna())) else str(v).strip()

        code = _cell(idx_code)
        title = _cell(idx_title)
        ann = _cell(idx_ann)

        # stream
        stream_id = None
        sv = _cell(idx_stream)
        if sv is not None:
            try:
                stream_id = int(float(sv))
            except Exception:
                stream_id = default_stream
        else:
            stream_id = default_stream

        for ds in dates_list:
            yield Row(date=ds, code=code, title=title, annotation=ann, stream_id=stream_id)

# --------- sync into DB ---------

def sync_schedule_from_files(files: Iterable[str]) -> int:
    """
    XLSX с колонками: No | start_date | end_date | topic_code | title | annotation
    - Диапазоны дат раскрываются в отдельные дни.
    - topics обновляются только реальными title/annotation из файла.
    - session_days upsert по (date, stream_id).
    """
    added = 0
    with get_db_connection() as con:
        con.row_factory = None
        cur = con.cursor()
        for f in files:
            p = Path(f)
            default_stream = _detect_stream_from_filename(p)
            for r in _iter_xlsx(p, default_stream):
                topic_id = None
                if r.code:
                    cur.execute("INSERT OR IGNORE INTO topics(code) VALUES (?)", (r.code,))
                    if r.title is not None:
                        cur.execute("UPDATE topics SET title=? WHERE code=?", (r.title, r.code))
                    if r.annotation is not None:
                        cur.execute("UPDATE topics SET annotation=? WHERE code=?", (r.annotation, r.code))
                    row = cur.execute("SELECT id FROM topics WHERE code=?", (r.code,)).fetchone()
                    topic_id = int(row[0]) if row else None

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
