from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import bs4
import httpx
import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from .ai.summarizer import summarize_with_ai
from .audit.engine import DEFAULT_MAX_PAGES, audit_site
from .audit.engine_v2 import comprehensive_audit
from .config import get_config, save_config
from .data.models import AuditResult
from .reporting.excel import write_xlsx
from .reporting.pdf import write_pdf
from .utils.io import ensure_dir, write_json
from .utils.url import URLValidationError, validate_url

try:
    from .agents.coordinator import MultiAgentCoordinator
    _MULTI_AGENT_AVAILABLE = True
    _MULTI_AGENT_IMPORT_ERROR: Exception | None = None
except ModuleNotFoundError as exc:
    MultiAgentCoordinator = None  # type: ignore[assignment]
    _MULTI_AGENT_AVAILABLE = False
    _MULTI_AGENT_IMPORT_ERROR = exc

app = typer.Typer(help="TinySEO AI — Local SEO Audit Agent (Enhanced)")
console = Console()


@app.command()
def audit(
    url: str = typer.Argument(..., help="Website to audit (e.g., https://example.com)"),
    pages: int = typer.Option(DEFAULT_MAX_PAGES, "--pages", "-p", help="Max pages to scan"),
    out: Path = typer.Option(Path("reports"), "--out", "-o", help="Output folder"),
):
    """
    Crawl and run basic SEO checks. Writes JSON to reports/<slug>/summary.json
    """
    # BUGFIX: Validate URL to prevent SSRF attacks (See: BUGFIXES.md #2)
    try:
        url = validate_url(url)
    except URLValidationError as e:
        console.print(f"[red]Invalid URL:[/] {e}")
        raise typer.Exit(code=1)

    cfg = get_config()
    plan = cfg.plan
    if plan == "free" and pages > DEFAULT_MAX_PAGES:
        console.print(f"[yellow]Free plan limit {DEFAULT_MAX_PAGES} pages — using {DEFAULT_MAX_PAGES}.[/]")
        pages = DEFAULT_MAX_PAGES

    console.rule(f"[bold green]TinySEO AI — Audit[/]  [white]({plan.upper()} mode)")

    result: AuditResult = asyncio.run(audit_site(url, max_pages=pages))

    # Prepare output path
    slug = urlparse(result.site).netloc.replace(":", "_")
    target_dir = (out / slug)
    ensure_dir(target_dir)
    out_json = target_dir / "summary.json"
    write_json(out_json, json.loads(result.model_dump_json()))

    # Pretty print summary
    table = Table(title=f"Summary — {result.site}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Pages scanned", str(result.pages_scanned))
    table.add_row("Issues found", str(len(result.issues)))
    console.print(table)

    # Show top 10 issues
    top = result.issues[:10]
    if top:
        it = Table(title="Sample issues (first 10)")
        it.add_column("Type", style="magenta")
        it.add_column("Severity", style="red")
        it.add_column("URL", style="white", overflow="fold")
        for iss in top:
            it.add_row(iss.type, iss.severity, iss.url)
        console.print(it)

    console.print(f"📁 Saved: [bold]{out_json}[/]")


@app.command("audit-full")
def audit_full(
    url: str = typer.Argument(..., help="Website to audit (e.g., https://example.com)"),
    pages: int = typer.Option(DEFAULT_MAX_PAGES, "--pages", "-p", help="Max pages to scan"),
    out: Path = typer.Option(Path("reports"), "--out", "-o", help="Output folder"),
    fast: bool = typer.Option(False, "--fast", help="Skip comprehensive checks for faster audit"),
):
    """
    Comprehensive SEO audit with all checks (security, performance, content quality, etc.)
    """
    # BUGFIX: Validate URL to prevent SSRF attacks (See: BUGFIXES.md #2)
    try:
        url = validate_url(url)
    except URLValidationError as e:
        console.print(f"[red]Invalid URL:[/] {e}")
        raise typer.Exit(code=1)

    cfg = get_config()
    plan = cfg.plan
    if plan == "free" and pages > DEFAULT_MAX_PAGES:
        console.print(f"[yellow]Free plan limit {DEFAULT_MAX_PAGES} pages — using {DEFAULT_MAX_PAGES}.[/]")
        pages = DEFAULT_MAX_PAGES

    console.rule(f"[bold green]TinySEO AI — Comprehensive Audit[/]  [white]({plan.upper()} mode)")

    if not fast:
        console.print("[cyan]Running full audit with all checks (security, performance, content, links)...[/]")

    result: AuditResult = asyncio.run(
        comprehensive_audit(url, max_pages=pages, enable_all_checks=not fast)
    )

    # Prepare output path
    slug = urlparse(result.site).netloc.replace(":", "_")
    target_dir = out / slug
    ensure_dir(target_dir)
    out_json = target_dir / "comprehensive_summary.json"
    write_json(out_json, json.loads(result.model_dump_json()))

    # Pretty print summary with health score
    table = Table(title=f"Comprehensive Audit — {result.site}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Pages scanned", str(result.pages_scanned))
    table.add_row("Total issues", str(len(result.issues)))

    # Show health score if available
    if "health_score" in result.meta:
        health_score = result.meta["health_score"]
        health_grade = result.meta.get("health_grade", "?")
        score_color = "green" if health_score >= 80 else "yellow" if health_score >= 60 else "red"
        table.add_row("Health Score", f"[{score_color}]{health_score}/100 (Grade: {health_grade})[/{score_color}]")

    if "robots_txt_exists" in result.meta:
        table.add_row("Robots.txt", "✓ Found" if result.meta["robots_txt_exists"] else "✗ Missing")

    if "sitemaps_found" in result.meta:
        table.add_row("Sitemaps", str(result.meta["sitemaps_found"]))

    console.print(table)

    # Show issues by severity
    severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
    for issue in result.issues:
        severity_counts[issue.severity] += 1

    if any(severity_counts.values()):
        sev_table = Table(title="Issues by Severity")
        sev_table.add_column("Severity", style="bold")
        sev_table.add_column("Count", style="white")

        if severity_counts["high"] > 0:
            sev_table.add_row("[red]High[/]", str(severity_counts["high"]))
        if severity_counts["medium"] > 0:
            sev_table.add_row("[yellow]Medium[/]", str(severity_counts["medium"]))
        if severity_counts["low"] > 0:
            sev_table.add_row("[blue]Low[/]", str(severity_counts["low"]))
        if severity_counts["info"] > 0:
            sev_table.add_row("[dim]Info[/]", str(severity_counts["info"]))

        console.print(sev_table)

    # Show top recommendations if available
    if "top_recommendations" in result.meta and result.meta["top_recommendations"]:
        rec_table = Table(title="Top Priority Fixes")
        rec_table.add_column("Issue Type", style="magenta")
        rec_table.add_column("Impact", style="red")
        rec_table.add_column("Effort", style="yellow")
        rec_table.add_column("Priority", style="green")

        for rec in result.meta["top_recommendations"][:5]:
            rec_table.add_row(
                rec["issue_type"].replace("_", " ").title(),
                f"{rec['impact']:.1f}",
                f"{rec['effort']:.1f}",
                f"{rec['priority']:.1f}"
            )

        console.print(rec_table)

    console.print(f"📁 Saved: [bold]{out_json}[/]")


@app.command("audit-ai")
def audit_ai(
    url: str = typer.Argument(..., help="Website to audit (e.g., https://example.com)"),
    pages: int = typer.Option(DEFAULT_MAX_PAGES, "--pages", "-p", help="Max pages to scan"),
    out: Path = typer.Option(Path("reports"), "--out", "-o", help="Output folder"),
    no_fixes: bool = typer.Option(False, "--no-fixes", help="Skip code fix generation"),
):
    """
    🤖 AI-Powered Multi-Agent SEO Audit

    Runs comprehensive audit with specialized AI agents:
    - Orchestrator Agent (coordinates analysis)
    - Technical SEO Agent (security, robots.txt, HTTPS)
    - Content Quality Agent (titles, meta, headings)
    - Performance Agent (speed, images, Core Web Vitals)
    - Link Analysis Agent (broken links, site architecture)
    - Fix Generator Agent (production-ready code fixes)

    Requires: OPENAI_API_KEY environment variable
    """
    # BUGFIX: Validate URL to prevent SSRF attacks (See: BUGFIXES.md #2)
    try:
        url = validate_url(url)
    except URLValidationError as e:
        console.print(f"[red]Invalid URL:[/] {e}")
        raise typer.Exit(code=1)

    cfg = get_config()

    if not _MULTI_AGENT_AVAILABLE:
        console.print("[red]Optional AI agent stack not installed.[/]")
        console.print(
            "Install LangChain dependencies to run this command:\n"
            "  pip install \"langchain>=0.1\" \"langchain-openai>=0.0.5\" \"langchain-anthropic>=0.1\"\n"
            "or run: pip install -r requirements.txt"
        )
        if _MULTI_AGENT_IMPORT_ERROR:
            console.print(f"[dim]Import error: {_MULTI_AGENT_IMPORT_ERROR}[/]")
        raise typer.Exit(code=1)

    # Check for API key
    if not cfg.openai_api_key:
        console.print("[red]Error:[/] OPENAI_API_KEY not found")
        console.print("\nTo use AI agents, add your OpenAI API key to .env file:")
        console.print("  echo 'OPENAI_API_KEY=sk-...' >> .env")
        console.print("\nOr set as environment variable:")
        console.print("  export OPENAI_API_KEY='sk-...'")
        console.print("\nVerify configuration:")
        console.print("  python test_env_config.py")
        raise typer.Exit(code=1)

    plan = cfg.plan
    if plan == "free" and pages > DEFAULT_MAX_PAGES:
        console.print(f"[yellow]Free plan limit {DEFAULT_MAX_PAGES} pages — using {DEFAULT_MAX_PAGES}.[/]")
        pages = DEFAULT_MAX_PAGES

    console.rule(f"[bold magenta]🤖 TinySEO AI — Multi-Agent Analysis[/]  [white]({plan.upper()} mode)")
    console.print("[cyan]Initializing AI agents...[/]\n")

    # Phase 1: Run comprehensive audit
    console.print("📊 [bold]Phase 1:[/] Running comprehensive SEO audit...")
    result: AuditResult = asyncio.run(
        comprehensive_audit(url, max_pages=pages, enable_all_checks=True)
    )

    # Save base audit results
    slug = urlparse(result.site).netloc.replace(":", "_")
    target_dir = out / slug
    ensure_dir(target_dir)
    out_json = target_dir / "comprehensive_summary.json"
    write_json(out_json, json.loads(result.model_dump_json()))

    console.print(f"✅ Audit complete: {len(result.issues)} issues found\n")

    # Phase 2: Multi-agent analysis
    console.print("🤖 [bold]Phase 2:[/] Deploying specialist AI agents...")

    coordinator = MultiAgentCoordinator(
        openai_api_key=cfg.openai_api_key,
        anthropic_api_key=cfg.anthropic_api_key,
    )

    try:
        agent_analysis = asyncio.run(
            coordinator.analyze_with_agents(result, enable_fix_generation=not no_fixes)
        )

        # Save agent analysis
        agent_json = target_dir / "agent_analysis.json"
        with open(agent_json, "w") as f:
            json.dump(agent_analysis, f, indent=2)

        console.print("\n✅ Multi-agent analysis complete!\n")

        # Display results
        # Summary table
        summary_table = Table(title=f"🎯 Analysis Summary — {result.site}")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        summary_table.add_row("Pages Scanned", str(result.pages_scanned))
        summary_table.add_row("Issues Found", str(len(result.issues)))
        summary_table.add_row("Health Score", f"{result.meta.get('health_score', 0)}/100")
        summary_table.add_row("Agents Deployed", str(len(agent_analysis.get('specialist_analysis', {}))))
        summary_table.add_row("Total Tokens Used", str(agent_analysis.get('total_tokens', 0)))
        summary_table.add_row("Avg Confidence", f"{agent_analysis.get('average_confidence', 0):.1%}")
        console.print(summary_table)

        # Key insights
        insights = agent_analysis.get('key_insights', [])
        if insights:
            console.print("\n💡 [bold]Key Insights:[/]")
            for i, insight in enumerate(insights[:5], 1):
                console.print(f"  {i}. {insight}")

        # Top recommendations
        top_recs = agent_analysis.get('top_recommendations', [])
        if top_recs:
            rec_table = Table(title="\n🔧 Top Priority Recommendations")
            rec_table.add_column("Priority", style="yellow")
            rec_table.add_column("Recommendation", style="white")
            rec_table.add_column("Impact", style="green")
            rec_table.add_column("Effort", style="blue")

            for rec in top_recs[:5]:
                priority_score = rec.get('impact', 0) / max(rec.get('effort', 1), 0.1)
                rec_table.add_row(
                    f"{priority_score:.1f}",
                    rec.get('title', 'N/A')[:50],
                    f"{rec.get('impact', 0):.1f}",
                    f"{rec.get('effort', 0):.1f}",
                )

            console.print(rec_table)

        # Chain of thought summary
        cot_summary = agent_analysis.get('chain_of_thought_summary', [])
        if cot_summary:
            console.print("\n🧠 [bold]Agent Reasoning Summary:[/]")
            for cot in cot_summary:
                console.print(
                    f"  • {cot['agent']}: {cot['steps']} reasoning steps "
                    f"({cot['confidence']:.1%} confidence, {cot['reasoning_time_ms']:.0f}ms)"
                )

        console.print("\n📁 Results saved:")
        console.print(f"  • Audit: [bold]{out_json}[/]")
        console.print(f"  • AI Analysis: [bold]{agent_json}[/]")

        # Show agent stats
        stats = coordinator.get_agent_stats()
        console.print("\n📊 [bold]Agent Performance:[/]")
        for agent_name, agent_stats in stats.items():
            console.print(
                f"  • {agent_name}: {agent_stats['tasks_completed']} tasks, "
                f"avg {agent_stats['average_task_time_ms']:.0f}ms"
            )

    except Exception as e:
        console.print(f"\n[red]❌ Agent analysis failed:[/] {e}")
        console.print("\nBase audit results were saved successfully.")
        console.print("Run with --help for more information.")
        raise typer.Exit(code=1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Print current config"),
    plan: str = typer.Option(None, "--plan", help="Force plan (free/premium) for local testing"),
):
    """
    Manage local config stored at ~/.config/tinyseoai/config.json
    """
    cfg = get_config()
    if plan:
        cfg.plan = plan
        save_config(cfg)
    if show or plan:
        console.print(cfg.model_dump_json(indent=2))


@app.command()
def doctor():
    """Quick environment check."""
    table = Table(title="Environment")
    table.add_column("Check")
    table.add_column("Status")
    table.add_row("Python", f"{sys.version.split()[0]}")
    table.add_row("httpx", httpx.__version__)
    table.add_row("BeautifulSoup", getattr(bs4, "__version__", "unknown"))
    console.print(table)
    console.print("[green]OK[/] — try: tinyseoai audit https://example.com")

# --- NEW: AI summary command -----------------------------------------------


@app.command()
def explain(
    json_report: Path = typer.Argument(..., help="Path to a previous summary.json"),
    out: Path = typer.Option(None, "--out", "-o", help="Output file (default: alongside input)"),
):
    """
    Use OpenAI to produce an executive summary & recommended actions
    from an existing crawl JSON (summary.json).
    """
    console.rule("[bold blue]AI Summary[/]")
    if not json_report.exists():
        typer.echo(f"File not found: {json_report}")
        raise typer.Exit(code=2)

    try:
        raw = json.loads(json_report.read_text())
        result = AuditResult(**raw)
    except (json.JSONDecodeError, ValidationError) as e:
        typer.echo(f"Invalid report JSON: {e}")
        raise typer.Exit(code=2)

    try:
        ai = summarize_with_ai(result)
    except Exception as e:
        console.print(f"[red]AI summary failed:[/] {e}")
        raise typer.Exit(code=1)

    # Write output next to input by default
    if out is None:
        out = json_report.parent / "summary_with_ai.json"

    with open(out, "w") as f:
        json.dump(ai, f, indent=2)

    # Console preview
    table = Table(title="Executive Summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white", overflow="fold")
    summary = ai.get("summary", "")[:400]
    table.add_row("Site", ai.get("site", ""))
    table.add_row("Summary", summary)
    table.add_row("Top issues", str(len(ai.get("top_issues", []))))
    table.add_row("Actions", str(len(ai.get("recommended_actions", []))))
    console.print(table)

    console.print(f"🧠 Saved AI summary → [bold]{out}[/]")


# --- REPORT export (xlsx/pdf) ------------------------------------------------


@app.command()
def report(
    src: Path = typer.Argument(..., help="Folder containing summary.json OR path to summary.json"),
    format: str = typer.Option("xlsx", "--format", "-f", help="Report format: xlsx|pdf"),
    out: Path = typer.Option(None, "--out", "-o", help="Output file path"),
    ai: bool = typer.Option(False, "--with-ai", help="Generate AI summary on the fly (uses your OpenAI key)"),
):
    """
    Build a client-friendly report (XLSX or PDF).
    - Reads summary.json
    - If summary_with_ai.json exists OR --with-ai is set, merges AI results under 'ai_summary'
    """
    console.rule("[bold green]Build Report[/]")

    # Accept either a folder (containing summary.json) or a direct summary.json path
    summary_path = src
    if summary_path.is_dir():
        summary_path = summary_path / "summary.json"
    if not summary_path.exists():
        console.print(f"[red]Missing report input:[/] {summary_path}")
        console.print("Hint: run 'tinyseoai audit <url>' or 'tinyseoai audit-report <url>' first.")
        raise typer.Exit(code=2)

    folder = summary_path.parent

    data = json.loads(summary_path.read_text())

    # Merge AI (cached or live)
    ai_path = folder / "summary_with_ai.json"
    merged_ai = None
    if ai_path.exists():
        try:
            merged_ai = json.loads(ai_path.read_text())
        except Exception:
            console.print("[yellow]Note:[/] Could not parse summary_with_ai.json, skipping cached AI.")

    if ai or merged_ai is None:
        try:
            from .data.models import AuditResult
            result = AuditResult(**data)
            merged_ai = summarize_with_ai(result)
            ai_path.write_text(json.dumps(merged_ai, indent=2))
        except Exception as e:
            console.print(f"[yellow]AI step skipped:[/] {e}")

    if merged_ai:
        data["ai_summary"] = merged_ai

    fmt = format.lower()
    site_slug = urlparse(data.get("site", "")).netloc or "site"

    if fmt == "xlsx":
        if out is None:
            out = folder / f"{site_slug}-report.xlsx"
        path = write_xlsx(data, out)
        console.print(f"📦 XLSX saved → [bold]{path}[/]")
    elif fmt == "pdf":
        if out is None:
            out = folder / f"{site_slug}-report.pdf"
        path = write_pdf(data, out)
        console.print(f"🖨️ PDF saved → [bold]{path}[/]")
    else:
        console.print("[red]Unsupported format. Use xlsx or pdf.[/]")
        raise typer.Exit(code=2)

# --- NEW: one-shot pipeline --------------------------------------------------
@app.command("audit-report")
def audit_report(
    url: str = typer.Argument(..., help="Site to audit (e.g., https://example.com)"),
    pages: int = typer.Option(DEFAULT_MAX_PAGES, "--pages", "-p", help="Max pages to scan"),
    outdir: Path = typer.Option(Path("reports"), "--outdir", "-o", help="Reports root folder"),
    format: str = typer.Option("pdf", "--format", "-f", help="Report format: pdf|xlsx"),
    with_ai: bool = typer.Option(True, "--with-ai/--no-ai", help="Include AI summary"),
):
    """
    Crawl -> explain (AI) -> export report in one shot.
    Writes to reports/<slug>/{summary.json, summary_with_ai.json, <slug>-report.(pdf|xlsx)}
    """
    # BUGFIX: Validate URL to prevent SSRF attacks (See: BUGFIXES.md #2)
    try:
        url = validate_url(url)
    except URLValidationError as e:
        console.print(f"[red]Invalid URL:[/] {e}")
        raise typer.Exit(code=1)

    console.rule("[bold green]Audit → Explain → Report[/]")

    # 1) audit
    result: AuditResult = asyncio.run(audit_site(url, max_pages=pages))
    slug = urlparse(result.site).netloc.replace(":", "_")
    folder = outdir / slug
    ensure_dir(folder)
    summary_path = folder / "summary.json"
    write_json(summary_path, json.loads(result.model_dump_json()))
    console.print(f"✅ Audit saved → [bold]{summary_path}[/]")

    # 2) explain (AI)
    merged_ai = None
    if with_ai:
        try:
            from .ai.summarizer import summarize_with_ai
            merged_ai = summarize_with_ai(result)
            (folder / "summary_with_ai.json").write_text(json.dumps(merged_ai, indent=2))
            console.print("🧠 AI summary saved → summary_with_ai.json")
        except Exception as e:
            console.print(f"[yellow]AI step skipped:[/] {e}")

    # 3) report
    data = json.loads(summary_path.read_text())
    if merged_ai:
        data["ai_summary"] = merged_ai

    site_slug = urlparse(data.get("site", "")).netloc or "site"
    if format.lower() == "pdf":
        from .reporting.pdf import write_pdf
        out_path = folder / f"{site_slug}-report.pdf"
        write_pdf(data, out_path)
        console.print(f"🖨️ PDF saved → [bold]{out_path}[/]")
    elif format.lower() == "xlsx":
        from .reporting.excel import write_xlsx
        out_path = folder / f"{site_slug}-report.xlsx"
        write_xlsx(data, out_path)
        console.print(f"📦 XLSX saved → [bold]{out_path}[/]")
    else:
        console.print("[red]Unsupported format. Use pdf or xlsx.[/]")
        raise typer.Exit(code=2)
