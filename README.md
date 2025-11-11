# TinySEO AI - Autonomous SEO Audit Agent

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**TinySEO AI** is an autonomous SEO audit agent that combines traditional rule-based checks with advanced AI-powered multi-agent analysis. The project now focuses entirely on the Python CLI experience for a leaner, easier-to-maintain toolchain.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Multi-Agent AI System](#multi-agent-ai-system)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Capabilities

- **Autonomous SEO Audits** – Crawl a site and capture issues across technical, content, and performance dimensions.
- **Multi-Agent AI System** – Five specialized AI agents generate insights and prioritized recommendations.
- **Multiple Report Formats** – Export JSON summaries plus Excel/PDF reports for stakeholders.
- **Deep Analysis** – Robots.txt, sitemaps, Core Web Vitals heuristics, link structure, and more.
- **Code Fix Generation** – Ready-to-apply snippets for common SEO problems.

### SEO Checks

- Meta tags (title, description, Open Graph)
- Content quality and readability signals
- Internal/external link analysis
- Image optimization and alt text
- Performance metrics and blocking assets
- Security headers and HTTPS verification
- Mobile responsiveness heuristics
- Sitemap and robots.txt validation
- Structured data/schema checks

---

## Installation

### Quick Install (CLI)

```bash
pip install tinyseoai
```

### From Source

```bash
git clone https://github.com/stalyndc/tinyseoai-cli.git
cd tinyseoai-cli
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ai]"
```

### Requirements

- **Python**: 3.12+
- **Playwright browsers** (optional, only for integration tests)
- **OpenAI / Anthropic API keys** for AI-powered commands
- **RAM**: 2GB recommended
- **Disk**: ~1GB for dependencies

---

## Quick Start

### Basic audit

```bash
tinyseoai audit https://example.com
```

### Comprehensive audit

```bash
tinyseoai audit-full https://example.com --pages 100
```

### AI-powered analysis

```bash
export OPENAI_API_KEY=sk-your-key
tinyseoai audit-ai https://example.com --pages 75
```

### Generate reports

```bash
tinyseoai report reports/example.com/summary.json --format pdf
tinyseoai report reports/example.com/summary.json --format xlsx
```

---

## Usage Examples

### Example 1: Quick CLI health check

```bash
tinyseoai audit https://myblog.com --pages 25
```

### Example 2: AI-first audit with fixes

```bash
tinyseoai audit-ai https://store.example --pages 80 --out reports/prod
```

### Example 3: Batch audits

```bash
#!/usr/bin/env bash
for site in acme.com shop.example docs.example; do
  tinyseoai audit-full "https://$site" --pages 60 --out reports
done
```

### Example 4: CI integration

```yaml
# .github/workflows/seo-audit.yml
name: SEO Audit
on:
  schedule:
    - cron: "0 6 * * 1"
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install tinyseoai
      - run: tinyseoai audit https://staging.example.com --pages 40 --out reports
```

---

## Multi-Agent AI System

TinySEO AI relies on **five specialized AI agents** that collaborate to provide comprehensive analysis:

### 1. Technical SEO Agent
- SSL/TLS configuration
- Security headers
- Robots.txt analysis
- Sitemap validation

### 2. Content Quality Agent
- Title and meta optimization
- Heading structure
- Content readability
- Keyword usage

### 3. Performance Agent
- Page load speed
- Core Web Vitals
- Image optimization
- Resource minification

### 4. Link Analysis Agent
- Broken link detection
- Internal linking structure
- External link quality
- Anchor text optimization

### 5. Fix Generator Agent
- Generates production-ready code
- Provides implementation steps
- Priority recommendations

**[Learn More About Agents](docs/AGENTS_README.md)**

---

## Output Examples

### CLI JSON Output

```json
{
  "url": "https://example.com",
  "health_score": 73,
  "metrics": {
    "pages_scanned": 15,
    "total_issues": 27,
    "critical_issues": 5
  },
  "issues": [
    {
      "severity": "critical",
      "category": "Meta Tags",
      "title": "Missing meta description",
      "description": "5 pages missing meta descriptions",
      "recommendation": "Add unique meta descriptions (150-160 chars)",
      "affected_pages": ["/about", "/contact"]
    }
  ]
}
```

---

## Documentation

- **[Quick Start](docs/QUICK_START.md)** – Step-by-step CLI walkthrough.
- **[Agents Guide](docs/AGENTS_README.md)** – Deep dive into the multi-agent system.
- **[Environment Setup](docs/ENV_SETUP_SUMMARY.md)** – Recommended tooling for contributors.
- **[Bug Fix Log](docs/BUGFIXES.md)** – Recent fixes and hardening notes.
- **[Upgrade Notes](docs/UPGRADE_PYTHON.md)** – Python compatibility guidance.

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TINYSEOAI_AGENT_PLAN=premium
```

### Config File

The CLI stores preferences at `~/.config/tinyseoai/config.json`. Edit it to change defaults such as plan, output directories, or agent settings.

### Pre-commit and Tests

```bash
pip install pre-commit
pre-commit install
pytest --maxfail=1 --disable-warnings -q
```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Install dependencies with `pip install -e ".[dev,ai]"`.
3. Run `ruff check tinyseoai`, `black tinyseoai`, and `pytest` before opening a PR.
4. Document user-facing changes in `README.md` or `docs/` as appropriate.

---

## Roadmap

- [x] Python CLI with basic audits
- [x] Multi-agent AI system
- [x] Excel and PDF reports
- [ ] Browser extension
- [ ] Cloud-based dashboard
- [ ] Team collaboration features
- [ ] Historical tracking
- [ ] Competitor analysis
- [ ] Mobile app companion

---

## Support

- **Documentation** – See the guides listed above.
- **Bug reports** – [GitHub Issues](https://github.com/stalyndc/tinyseoai-cli/issues).
- **Questions** – [GitHub Discussions](https://github.com/stalyndc/tinyseoai-cli/discussions).
- **Email** – support@tinyseoai.com.

### Troubleshooting

1. **CLI not found** – Ensure Python scripts directory is on PATH.
2. **Playwright errors** – Install browsers with `playwright install chromium`.
3. **AI commands fail** – Confirm `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set.

---

## Performance

| Mode | Startup Time | Memory Usage | Notes |
|------|--------------|--------------|-------|
| CLI audit | < 1s | ~50 MB | Pure Python, fast startup |
| AI audit | < 2s | ~65 MB | Includes LangChain + LLM clients |
| Report generation | < 1s | ~40 MB | Generates Excel/PDF outputs |

---

## Why TinySEO AI?

### vs Traditional SEO Tools

- **Autonomous** – Multi-agent AI digs deeper than simple rule checks.
- **Open Source** – Inspect, extend, and self-host.
- **Local First** – Crawl sites privately without external services.
- **Automation Friendly** – Scriptable CLI plus JSON/Excel/PDF outputs.

### vs Other CLI Tools

- **AI Recommendations** – Prioritized fixes, not just warnings.
- **Code Generation** – Concrete snippets for developers.
- **Modern Stack** – Async crawler, Pydantic models, Rich CLI UX.
- **Active Roadmap** – Regular bug fixes and feature drops.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with amazing open-source tools:

- **[LangChain](https://langchain.com)** – AI orchestration.
- **[Typer](https://typer.tiangolo.com)** – CLI framework.
- **[Rich](https://rich.readthedocs.io)** – Terminal formatting.
- **[Playwright](https://playwright.dev)** – Browser automation for reports.

---

## Get Started Now!

```bash
pip install tinyseoai
tinyseoai audit-ai https://your-site.com
```

Happy auditing!
