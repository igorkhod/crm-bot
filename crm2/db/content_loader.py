# crm2/db/content_loader.py
# Назначение: Синхронизация контента из markdown-файлов (pages и news) в базу данных
# Функции:
# - _parse_md - Парсит markdown-файл, извлекая заголовок (из первой строки с #) и тело
# - sync_content_from_files - Синхронизирует страницы и новости из папок content/pages и content/news в таблицы pages и news

from __future__ import annotations
import re, datetime as dt
from pathlib import Path
from crm2.db.core import get_db_connection

H1_RE = re.compile(r"^#\s+(.*)$")

def _parse_md(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    title = ""
    body  = text
    if lines:
        m = H1_RE.match(lines[0])
        if m:
            title = m.group(1).strip()
            body  = "\n".join(lines[1:]).strip()
    if not title:
        title = path.stem
    return title, body

def sync_content_from_files(base: str = "content") -> tuple[int,int]:
    base_dir = Path(base)
    pages_dir = base_dir / "pages"
    news_dir  = base_dir / "news"
    pages_dir.mkdir(parents=True, exist_ok=True)
    news_dir.mkdir(parents=True,  exist_ok=True)

    up_pages = up_news = 0
    # pages
    with get_db_connection() as con:
        cur = con.cursor()
        for p in sorted(pages_dir.glob("*.md")):
            slug = p.stem  # contacts.md -> 'contacts'
            title, body = _parse_md(p)
            cur.execute("""
              INSERT INTO pages(slug, title, body)
              VALUES (?, ?, ?)
              ON CONFLICT(slug) DO UPDATE
              SET title=excluded.title, body=excluded.body, updated_at=CURRENT_TIMESTAMP
            """, (slug, title, body))
            up_pages += 1

        # news
        for n in sorted(news_dir.glob("*.md")):
            name = n.stem  # '2025-09-01__my-news' or 'PINNED__2025-09-01__my-news'
            pinned = 0
            parts = name.split("__")
            if parts[0].upper() == "PINNED":
                pinned = 1
                parts = parts[1:]
            if len(parts) < 2:
                # fallback: no date — пропускаем
                continue
            date_str, slug = parts[0], "__".join(parts[1:])
            try:
                pub = dt.date.fromisoformat(date_str)
            except ValueError:
                continue
            title, body = _parse_md(n)
            cur.execute("""
              INSERT INTO news(slug, title, body, published_at, is_pinned)
              VALUES (?, ?, ?, ?, ?)
              ON CONFLICT(slug) DO UPDATE
              SET title=excluded.title, body=excluded.body, published_at=excluded.published_at, is_pinned=excluded.is_pinned
            """, (slug, title, body, pub.isoformat(), pinned))
            up_news += 1
        con.commit()
    return up_pages, up_news
