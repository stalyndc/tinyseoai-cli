from __future__ import annotations

import base64
from datetime import datetime
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import get_config


def _templates_path() -> str:
    """Return a real filesystem path to the templates dir.

    Using importlib.resources.files returns a Traversable (e.g., MultiplexedPath)
    whose str() is not a usable filesystem path for Jinja's FileSystemLoader.
    Resolve relative to this file instead.
    """
    return str((Path(__file__).parent / "templates").resolve())


def _font_base64() -> str | None:
    # Try to read font from package dir on disk; fall back to importlib.resources
    # if needed. Return None if not found.
    candidates = [
        Path(__file__).parent / "fonts" / "WorkSans-Regular.ttf",
    ]
    for p in candidates:
        try:
            if p.exists():
                return base64.b64encode(p.read_bytes()).decode("ascii")
        except Exception:
            pass
    try:
        font_pkg = "tinyseoai.reporting.fonts"
        font_path = importlib_resources.files(font_pkg) / "WorkSans-Regular.ttf"
        with importlib_resources.as_file(font_path) as f:
            return base64.b64encode(Path(f).read_bytes()).decode("ascii")
    except Exception:
        return None


def build_html(summary: dict[str, Any]) -> str:
    cfg = get_config()
    env = Environment(
        loader=FileSystemLoader(_templates_path()),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template("report.html")
    site = summary.get("site", "")
    ctx = {
        "title": f"{cfg.brand.name} Report",
        "subtitle": site,
        "ts": datetime.utcnow().isoformat() + "Z",
        "site": site,
        "pages_scanned": summary.get("pages_scanned", 0),
        "issues": summary.get("issues", []),
        "meta": summary.get("meta", {}),
        "ai": summary.get("ai_summary"),
        "font_data": _font_base64(),
        "brand": {
            "name": cfg.brand.name,
            "accent_hex": cfg.brand.accent_hex,
            "show_bot_logo": cfg.brand.show_bot_logo,
        },
    }
    return tpl.render(**ctx)
