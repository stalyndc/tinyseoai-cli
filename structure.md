tinyseoai/
├─ .gitignore
├─ LICENSE
├─ README.md
├─ requirements.txt
├─ pyproject.toml                # build/metadata (entrypoint later)
├─ .env.example                  # local dev (API base, etc.)
├─ reports/                      # output dir (gitkeep)
│  └─ .gitkeep
├─ examples/
│  ├─ sample_config.json
│  └─ sample_urls.txt
├─ scripts/                      # packaging/build helpers
│  ├─ build_macos.sh
│  ├─ build_linux.sh
│  └─ build_windows.ps1
├─ docs/
│  ├─ AGENTS.md                  # prompts/roles for Codex/Claude
│  └─ ROADMAP.md
└─ tinyseoai/                    # PYTHON PACKAGE (CLI)
   ├─ __init__.py
   ├─ __main__.py                # allows: python -m tinyseoai
   ├─ version.py
   ├─ cli.py                     # Typer entrypoint: audit/explain/report/activate
   ├─ config.py                  # pydantic config + platformdirs (stores ~/.config/tinyseoai/)
   ├─ utils/
   │  ├─ __init__.py
   │  ├─ logging.py
   │  ├─ url.py
   │  ├─ io.py
   │  └─ concurrency.py
   ├─ data/
   │  ├─ __init__.py
   │  ├─ models.py               # pydantic models for issues, results
   │  └─ scoring.py              # impact×effort scoring rules
   ├─ audit/
   │  ├─ __init__.py
   │  ├─ crawler.py              # httpx async crawl, sitemap/queue
   │  ├─ robots.py               # robots.txt + politeness
   │  ├─ parser.py               # trafilatura/bs4/lxml helpers
   │  └─ checks/                 # rule-based SEO checks
   │     ├─ __init__.py
   │     ├─ meta.py              # title/meta/h1 lengths, duplicates
   │     ├─ links.py             # broken links, mixed content
   │     ├─ indexability.py      # canonical, noindex, sitemap presence
   │     ├─ performance.py       # basic weight/large images heuristics
   │     └─ duplicates.py        # duplicate titles/descriptions
   ├─ ai/
   │  ├─ __init__.py
   │  ├─ openai_client.py        # wrapper; swaps free vs premium model
   │  └─ summarizer.py           # exec summary + prioritized actions
   ├─ reporting/
   │  ├─ __init__.py
   │  ├─ templates/
   │  │  ├─ base.html            # Jinja base (shared styles)
   │  │  └─ report.html          # full HTML report
   │  ├─ html_report.py          # builds HTML from JSON results
   │  ├─ pdf.py                  # HTML→PDF (playwright or weasyprint)
   │  └─ excel.py                # XLSX via openpyxl/xlsxwriter
   └─ licensing/
      ├─ __init__.py
      ├─ activation.py           # activate license, store token
      └─ machine.py              # simple machine fingerprint
