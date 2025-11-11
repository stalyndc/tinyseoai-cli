from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import base64

from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import importlib.resources as pkg_resources


def _templates_path() -> str:
    # Resolve templates directory relative to this file to ensure a real
    # filesystem path for Jinja's FileSystemLoader.
    return str((Path(__file__).parent / "templates").resolve())

def _font_base64() -> str | None:
    try:
        font_pkg = "tinyseoai.reporting.fonts"
        font_path = pkg_resources.files(font_pkg) / "WorkSans-Regular.woff2"
        b = font_path.read_bytes()
        return base64.b64encode(b).decode("ascii")
    except Exception:
        return None

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
        "font_data": _font_base64(),
    }
    return tpl.render(**ctx)
