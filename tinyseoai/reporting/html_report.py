from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _templates_path() -> str:
    # Resolve the templates folder relative to this file
    from pathlib import Path
    current_file = Path(__file__).resolve()
    return str(current_file.parent / "templates")


def build_html(summary: Dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(_templates_path()),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template("report.html")
    site = summary.get("site", "")
    ctx = {
        "title": "TinySEO AI Report",
        "subtitle": site,
        "ts": datetime.utcnow().isoformat() + "Z",
        "site": site,
        "pages_scanned": summary.get("pages_scanned", 0),
        "issues": summary.get("issues", []),
        "meta": summary.get("meta", {}),
        "ai": summary.get("ai_summary"),
    }
    return tpl.render(**ctx)
