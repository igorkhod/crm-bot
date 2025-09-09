# crm2/services/content_loader.py
from pathlib import Path
from typing import Literal
import re

try:
    import markdown as _md
except Exception:
    _md = None

ContentKey = Literal["mode", "meanings"]

_BASE = Path(__file__).resolve().parents[1] / "content" / "info"
_FILES = {
    "mode":     _BASE / "mode.md",
    "meanings": _BASE / "meanings.md",
}

_ALLOWED = ("b", "i", "u", "s", "a", "code", "pre")

def _sanitize_html_for_telegram(html: str) -> str:
    """Привести Markdown-HTML к безопасному подмножеству Telegram HTML."""
    # Заголовки -> жирный + перевод строки
    for h in ("h1","h2","h3","h4","h5","h6"):
        html = re.sub(fr"<{h}[^>]*>(.*?)</{h}>", r"<b>\1</b>\n", html, flags=re.S|re.I)
    # Параграфы -> текст + \n
    html = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n", html, flags=re.S|re.I)
    # Списки: <li> -> "• ...\n", убираем обёртки <ul>/<ol>
    html = re.sub(r"<li[^>]*>(.*?)</li>", r"• \1\n", html, flags=re.S|re.I)
    html = re.sub(r"</?(ul|ol)[^>]*>", "", html, flags=re.I)
    # Сильное/курсив -> допустимые теги
    html = re.sub(r"</?strong>", lambda m: "</b>" if m.group(0).startswith("</") else "<b>", html, flags=re.I)
    html = re.sub(r"</?em>",     lambda m: "</i>" if m.group(0).startswith("</") else "<i>", html, flags=re.I)
    # <br> нормализуем к \n
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    # Удаляем все прочие теги, кроме разрешённых
    def _strip_unknown(tag_match):
        tag = tag_match.group(0)
        name = re.sub(r"[</>\s].*$", "", tag[1:]).lower()
        return tag if name in _ALLOWED else ""
    html = re.sub(r"</?[^>]+>", _strip_unknown, html)
    # Сжимаем лишние пустые строки
    html = re.sub(r"\n{3,}", "\n\n", html).strip()
    return html

def load_html(key: ContentKey) -> str:
    path = _FILES[key]
    if not path.exists():
        return "<b>Текст временно недоступен.</b>"
    text = path.read_text(encoding="utf-8")
    if _md is None:
        from html import escape
        return f"<pre>{escape(text)}</pre>"
    html = _md.markdown(text, extensions=["extra", "sane_lists"])
    return _sanitize_html_for_telegram(html)
