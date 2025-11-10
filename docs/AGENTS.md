# 🤖 TinySEO AI — Codex / Builder Agent Instructions

You are an **AI software engineer** collaborating on the project **tinyseoai-cli**.
The goal is to build a cross-platform SEO auditing agent (CLI) written in **Python**.

---

## 🎯 Mission

Create a local-first CLI tool that:

1. Audits a website (crawl, parse, detect issues)
2. Generates reports (JSON → PDF/XLSX)
3. Uses OpenAI for explanations and summaries
4. Connects later to api.tinyseoai.com for licensing

---

## 🏗️ Folder you’re working in

`tinyseoai/` — main Python package.

Key files:

- `cli.py` → Typer entry point (`audit`, `explain`, `report`, `activate`)
- `audit/` → crawling, parsing, and rule-based checks
- `ai/` → OpenAI integration (free vs premium)
- `reporting/` → report generators (HTML→PDF, Excel)
- `data/models.py` → Pydantic models for issues & results
- `config.py` → loads and saves ~/.config/tinyseoai/config.json

---

## ⚙️ Tech Stack

- **Python 3.11+**
- Typer + Rich (CLI)
- Async HTTP via httpx
- trafilatura / lxml (content extraction)
- OpenAI API (GPT-4o mini for free, GPT-5 for premium)
- pandas + openpyxl (data)
- jinja2 + weasyprint/playwright (reports)
- pyinstaller for packaging

---

## 🧩 Commands (to implement)

tinyseoai audit <url> [--pages N] [--out ./reports/...]
tinyseoai explain <json_report>
tinyseoai report <folder> --format pdf|xlsx
tinyseoai activate <LICENSE_KEY>

---

## 🧠 Behavior

- Respect robots.txt.
- Crawl only same domain by default.
- Limit pages (default 50 for free).
- Save outputs under `./reports/<slug>/`.
- In free mode, use cheap model for summaries.
- All configuration in `~/.config/tinyseoai/config.json`.

---

## 🚀 Milestone 1 (MVP)

- Implement `audit` command with async crawl + 3 basic checks:
  1. Missing/duplicate title & meta description
  2. Broken internal links
  3. Noindex/canonical conflicts
- Output → `summary.json`
- Add minimal AI summary (`openai_client.py` stub).

---

Follow Python best practices, type hints, and include docstrings.
