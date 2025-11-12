# TinySEO AI CLI Commands Reference

This document provides a comprehensive reference for all TinySEO AI CLI commands and their options.

## Installation & Setup

```bash
# Install from PyPI
pip install tinyseoai

# Install from source (development)
git clone https://github.com/stalyndc/tinyseoai-cli.git
cd tinyseoai-cli
pip install -e ".[all]"
```

## Environment Configuration

Create a `.env` file in your project root:

```bash
# Required for AI-powered commands
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Optional: Anthropic Claude API key
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here

# Optional: Force plan tier
TINYSEOAI_AGENT_PLAN=premium
```

## Core Commands

### 1. `tinyseoai audit` - Basic SEO Audit

Run a basic SEO crawl with essential checks.

```bash
tinyseoai audit <URL> [OPTIONS]
```

**Arguments:**
- `URL` - Website to audit (e.g., https://example.com)

**Options:**
- `--pages, -p` - Maximum pages to scan (default: 50)
- `--out, -o` - Output folder (default: reports)

**Examples:**
```bash
# Basic audit with default settings
tinyseoai audit https://example.com

# Audit with custom page limit
tinyseoai audit https://example.com --pages 100

# Custom output directory
tinyseoai audit https://example.com --out my-reports
```

**Output:**
- JSON saved to `reports/<domain>/summary.json`
- Console summary with top issues

---

### 2. `tinyseoai audit-full` - Comprehensive SEO Audit

Run comprehensive audit with all checks (security, performance, content quality, links).

```bash
tinyseoai audit-full <URL> [OPTIONS]
```

**Arguments:**
- `URL` - Website to audit (e.g., https://example.com)

**Options:**
- `--pages, -p` - Maximum pages to scan (default: 50)
- `--out, -o` - Output folder (default: reports)
- `--fast` - Skip comprehensive checks for faster audit
- `--no-progress` - Disable progress bar

**Examples:**
```bash
# Full comprehensive audit
tinyseoai audit-full https://example.com

# Fast audit (skip some comprehensive checks)
tinyseoai audit-full https://example.com --fast

# Large site audit with no progress display
tinyseoai audit-full https://example.com --pages 200 --no-progress
```

**Output:**
- JSON saved to `reports/<domain>/comprehensive_summary.json`
- Health score and grade
- Issues categorized by severity
- Top priority recommendations

---

### 3. `tinyseoai audit-ai` - AI-Powered Multi-Agent Audit

🤖 **Premium Feature** - Deploy specialist AI agents for deep analysis.

```bash
tinyseoai audit-ai <URL> [OPTIONS]
```

**Arguments:**
- `URL` - Website to audit (e.g., https://example.com)

**Options:**
- `--pages, -p` - Maximum pages to scan (default: 50)
- `--out, -o` - Output folder (default: reports)
- `--no-fixes` - Skip code fix generation
- `--no-progress` - Disable progress bar

**Requirements:**
- `OPENAI_API_KEY` environment variable

**Multi-Agent System:**
1. **Orchestrator Agent** - Coordinates analysis workflow
2. **Technical SEO Agent** - Security, robots.txt, HTTPS analysis
3. **Content Quality Agent** - Titles, meta tags, headings analysis
4. **Performance Agent** - Page speed, images, Core Web Vitals
5. **Link Analysis Agent** - Broken links, site architecture
6. **Fix Generator Agent** - Production-ready code fixes

**Examples:**
```bash
# Full AI-powered audit with all agents
tinyseoai audit-ai https://example.com

# AI audit without fix generation (faster)
tinyseoai audit-ai https://example.com --no-fixes

# Large site AI audit
tinyseoai audit-ai https://example.com --pages 100
```

**Output:**
- Base audit: `reports/<domain>/comprehensive_summary.json`
- AI analysis: `reports/<domain>/agent_analysis.json`
- Agent performance metrics
- Key insights and recommendations
- Chain-of-thought reasoning summary

---

### 4. `tinyseoai explain` - AI Summary of Existing Report

Generate AI-powered executive summary from an existing audit report.

```bash
tinyseoai explain <JSON_REPORT> [OPTIONS]
```

**Arguments:**
- `JSON_REPORT` - Path to a previous summary.json file

**Options:**
- `--out, -o` - Output file path (default: alongside input)

**Requirements:**
- `OPENAI_API_KEY` environment variable

**Examples:**
```bash
# Generate AI summary of existing report
tinyseoai explain reports/example.com/summary.json

# Custom output location
tinyseoai explain reports/example.com/summary.json --out executive-summary.json
```

**Output:**
- Executive summary with key insights
- Top prioritized issues
- Recommended actions
- Saved as `summary_with_ai.json` or custom path

---

### 5. `tinyseoai report` - Generate Client Reports

Build client-friendly reports in XLSX or PDF format.

```bash
tinyseoai report <SRC> [OPTIONS]
```

**Arguments:**
- `SRC` - Folder containing summary.json OR direct path to summary.json

**Options:**
- `--format, -f` - Report format: xlsx|pdf (default: xlsx)
- `--out, -o` - Output file path
- `--with-ai` - Generate AI summary on the fly

**Examples:**
```bash
# Generate Excel report
tinyseoai report reports/example.com --format xlsx

# Generate PDF report
tinyseoai report reports/example.com --format pdf

# Include AI summary in report
tinyseoai report reports/example.com --with-ai

# Custom output path
tinyseoai report reports/example.com/summary.json --out my-report.xlsx
```

**Output:**
- Formatted report with charts and visualizations
- Merges AI summary if available
- Professional formatting for client delivery

---

### 6. `tinyseoai audit-report` - All-in-One Pipeline

Crawl → AI Analysis → Report generation in one command.

```bash
tinyseoai audit-report <URL> [OPTIONS]
```

**Arguments:**
- `URL` - Website to audit (e.g., https://example.com)

**Options:**
- `--pages, -p` - Maximum pages to scan (default: 50)
- `--outdir, -o` - Reports root folder (default: reports)
- `--format, -f` - Report format: pdf|xlsx (default: pdf)
- `--with-ai/--no-ai` - Include AI summary (default: True)

**Examples:**
```bash
# Full pipeline with PDF report and AI
tinyseoai audit-report https://example.com

# Excel report without AI
tinyseoai audit-report https://example.com --format xlsx --no-ai

# Custom output directory
tinyseoai audit-report https://example.com --outdir client-reports
```

**Output:**
- `summary.json` - Base audit results
- `summary_with_ai.json` - AI analysis (if enabled)
- `<domain>-report.pdf` or `.xlsx` - Final report

---

## Utility Commands

### 7. `tinyseoai config` - Configuration Management

Manage local configuration stored at `~/.config/tinyseoai/config.json`.

```bash
tinyseoai config [OPTIONS]
```

**Options:**
- `--show` - Print current configuration
- `--plan` - Force plan tier (free|premium) for local testing

**Examples:**
```bash
# Show current configuration
tinyseoai config --show

# Set plan to premium (for testing)
tinyseoai config --plan premium

# Reset to free plan
tinyseoai config --plan free
```

---

### 8. `tinyseoai doctor` - Environment Check

Quick environment and dependency verification.

```bash
tinyseoai doctor
```

**Output:**
- Python version
- Key dependency versions
- System compatibility check

---

## Command Workflows

### Quick Start Workflow
```bash
# 1. Environment setup
tinyseoai doctor

# 2. Basic audit
tinyseoai audit https://yoursite.com

# 3. Generate report
tinyseoai report reports/yoursite.com --format pdf
```

### AI-Powered Workflow
```bash
# 1. Set up API keys
export OPENAI_API_KEY=sk-your-key-here

# 2. Run comprehensive AI audit
tinyseoai audit-ai https://yoursite.com --pages 50

# 3. Generate client report
tinyseoai report reports/yoursite.com --with-ai --format pdf
```

### Batch Processing Workflow
```bash
#!/bin/bash
# Process multiple sites
SITES=("site1.com" "site2.com" "site3.com")

for site in "${SITES[@]}"; do
    echo "Auditing $site..."
    tinyseoai audit-report "https://$site" --format xlsx --with-ai
done
```

### CI/CD Integration
```bash
# GitHub Actions workflow
name: SEO Audit
on:
  schedule:
    - cron: "0 6 * * 1"  # Weekly
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install tinyseoai
      - run: tinyseoai audit https://staging.example.com --pages 40
```

## Plan Tiers

### Free Plan
- Up to 50 pages per audit
- Basic SEO checks
- Standard reporting formats

### Premium Plan
- Unlimited pages
- Multi-agent AI analysis
- Advanced recommendations
- Code fix generation
- Priority support

## Troubleshooting

### Common Issues

**Invalid URL Error:**
```bash
# Ensure URL includes protocol
tinyseoai audit https://example.com  # ✅ Correct
tinyseoai audit example.com          # ❌ Missing https://
```

**API Key Issues:**
```bash
# Verify API key is set
python test_env_config.py

# Or check manually
echo $OPENAI_API_KEY
```

**Module Import Errors:**
```bash
# Reinstall with all dependencies
pip install -e ".[all]"
```

**Permission Errors:**
```bash
# Ensure write permissions to output directory
chmod 755 reports/
```

### Debug Mode

Set environment variable for detailed logging:
```bash
export TINYSEOAI_DEBUG=1
tinyseoai audit https://example.com
```

## Performance Tips

1. **Large Sites**: Use `--pages` to limit crawl scope
2. **Fast Audits**: Use `audit-full --fast` for quicker scans
3. **Batch Processing**: Run audits in parallel for multiple sites
4. **Caching**: Results are cached in `reports/` directory

## Integration Examples

### Python Script Integration
```python
import asyncio
from tinyseoai.audit.engine_v2 import comprehensive_audit

async def audit_site():
    result = await comprehensive_audit(
        "https://example.com",
        max_pages=50,
        enable_all_checks=True
    )
    return result

# Run audit
result = asyncio.run(audit_site())
print(f"Found {len(result.issues)} issues")
```

### Webhook Integration
```bash
# Trigger audit via webhook
curl -X POST https://your-api.com/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "pages": 100}'
```

## Support

- **Documentation**: [docs/](./)
- **Issues**: [GitHub Issues](https://github.com/stalyndc/tinyseoai-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/stalyndc/tinyseoai-cli/discussions)
- **Email**: support@tinyseoai.com

---

*For the latest updates and features, visit the [GitHub repository](https://github.com/stalyndc/tinyseoai-cli).*
