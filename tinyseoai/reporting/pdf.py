from __future__ import annotations

from pathlib import Path

from .html_report import build_html


# We try Playwright first; if not available, fall back to WeasyPrint if installed.
def write_pdf(summary: dict, out_path: Path) -> Path:
    html = build_html(summary)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Playwright path
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            page.pdf(path=str(out_path), format="A4", print_background=True, margin={"top":"14mm","bottom":"14mm","left":"12mm","right":"12mm"})
            browser.close()
        return out_path
    except Exception as e:
        # Optional fallback to WeasyPrint
        try:
            from weasyprint import HTML  # type: ignore
            HTML(string=html).write_pdf(str(out_path))
            return out_path
        except Exception as e2:
            raise RuntimeError(f"PDF generation failed. Playwright error: {e}; WeasyPrint error: {e2}") from e
