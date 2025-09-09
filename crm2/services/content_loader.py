from pathlib import Path
from typing import Literal
try:
    import markdown as _md
except Exception:
    _md = None

ContentKey = Literal["mode", "meanings"]
_BASE = Path(__file__).resolve().parents[1] / "content" / "info"
_FILES = {
    "mode": _BASE / "mode.md",
    "meanings": _BASE / "meanings.md",
}

def load_html(key: ContentKey) -> str:
    path = _FILES[key]
    if not path.exists():
        return "<b>Текст временно недоступен.</b>"
    text = path.read_text(encoding="utf-8")
    if _md is None:
        from html import escape
        return f"<pre>{escape(text)}</pre>"
    return _md.markdown(text, extensions=["extra", "sane_lists"])
