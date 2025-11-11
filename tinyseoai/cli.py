from __future__ import annotations

import asyncio
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Set, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

import bs4
import httpx
import typer
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

from .config import get_config, save_config
from .data.models import Issue, AuditResult
from .utils.io import ensure_dir, write_json
from .utils.url import normalize_url, same_host

app = typer.Typer(help="TinySEO AI — Local SEO Audit Agent (MVP)")
console = Console()

DEFAULT_MAX_PAGES = 50

USER_AGENT = (
    "TinySEOAI/0.1 (+https://tinyseoai.com; cli) "
    "python-httpx"
)


@dataclass
class Page:
    url: str
    status: int = 0
    title: str | None = None
    meta_desc: str | None = None
    noindex: bool = False
    links: Set[str] = None


async def fetch(client: httpx.AsyncClient, url: str) -> Tuple[str, httpx.Response | None]:
    try:
        r = await client.get(url, timeout=15.0, follow_redirects=True)
        return url, r
    except Exception:
        return url, None


def extract_links(html: str, base: str) -> Set[str]:
    soup = BeautifulSoup(html, "lxml")
    out: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href").strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        absu = urljoin(base, href)
        out.add(normalize_url(absu))
    return out


def extract_meta(html: str) -> Tuple[str | None, str | None, bool]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else None

    md = None
    mdesc = soup.find("meta", attrs={"name": "description"})
    if mdesc and mdesc.get("content"):
        md = mdesc["content"].strip()

    # noindex detection
    noindex = False
    robots = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots and robots.get("content"):
        content = robots["content"].lower()
        if "noindex" in content:
            noindex = True

    return title, md, noindex


async def audit_site(seed_url: str, max_pages: int = DEFAULT_MAX_PAGES) -> AuditResult:
    seed_url = normalize_url(seed_url)
    origin = urlparse(seed_url)
    host = origin.netloc

    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"}

    visited: Set[str] = set()
    to_visit: deque[str]  # type: ignore
    from collections import deque
    to_visit = deque([seed_url])

    pages: list[Page] = []
    issues: list[Issue] = []

    async with httpx.AsyncClient(headers=headers, http2=True) as client:
        while to_visit and len(pages) < max_pages:
            url = to_visit.popleft()
            if url in visited:
                continue
            visited.add(url)

            _, resp = await fetch(client, url)
            if resp is None:
                issues.append(Issue(url=url, type="fetch_error", severity="high", detail="Request failed"))
                continue

            status = resp.status_code
            html = resp.text if resp.headers.get("content-type", "").startswith("text/html") else ""

            page = Page(url=url, status=status, links=set())
            if status >= 400:
                issues.append(Issue(url=url, type="http_error", severity="high", detail=f"Status {status}"))
            else:
                title, meta_desc, noindex = extract_meta(html)
                page.title = title
                page.meta_desc = meta_desc
                page.noindex = noindex

                # Simple checks
                if not title:
                    issues.append(Issue(url=url, type="title_missing", severity="medium"))
                elif len(title) > 60:
                    issues.append(Issue(url=url, type="title_too_long", severity="low", detail=str(len(title))))

                if not meta_desc:
                    issues.append(Issue(url=url, type="meta_description_missing", severity="low"))

                if noindex:
                    issues.append(Issue(url=url, type="noindex", severity="info"))

                # Link extraction and enqueue internal links
                links = extract_links(html, url)
                page.links = set()
                for link in links:
                    if same_host(link, host):
                        page.links.add(link)
                        if link not in visited and len(visited) + len(to_visit) < max_pages * 3:
                            to_visit.append(link)

                # Quick broken-link check for internal links (sampled)
                sample = list(page.links)[:10]
                for lnk in sample:
                    try:
                        r = await client.head(lnk, timeout=10.0, follow_redirects=True)
                        if r.status_code >= 400:
                            issues.append(Issue(url=url, type="broken_link", severity="medium", detail=lnk))
                    except Exception:
                        issues.append(Issue(url=url, type="broken_link", severity="medium", detail=lnk))

            pages.append(page)

    # Duplicate title check
    titles: dict[str, list[str]] = {}
    for p in pages:
        if p.title:
            titles.setdefault(p.title.strip().lower(), []).append(p.url)
    for t, urls in titles.items():
        if len(urls) > 1:
            for u in urls:
                issues.append(Issue(url=u, type="duplicate_title", severity="low", detail=t[:80]))

    return AuditResult(
        site=seed_url,
        pages_scanned=len(pages),
        issues=issues,
        meta={
            "max_pages": max_pages,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": "tinyseoai/0.1.0",
        },
    )


@app.command()
def audit(
    url: str = typer.Argument(..., help="Website to audit (e.g., https://example.com)"),
    pages: int = typer.Option(DEFAULT_MAX_PAGES, "--pages", "-p", help="Max pages to scan"),
    out: Path = typer.Option(Path("reports"), "--out", "-o", help="Output folder"),
):
    """
    Crawl and run basic SEO checks. Writes JSON to reports/<slug>/summary.json
    """
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
def explain(
    summary_path: Path = typer.Argument(..., help="Path to summary.json file"),
    use_ai: bool = typer.Option(False, "--ai", help="Use AI to explain issues (requires OPENAI_API_KEY)"),
):
    """
    Explain SEO audit results from a summary.json file.
    """
    if not summary_path.exists():
        console.print(f"[red]Error: File not found: {summary_path}[/]")
        raise typer.Exit(1)
    
    try:
        with open(summary_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        console.print(f"[red]Error: Invalid JSON file: {summary_path}[/]")
        raise typer.Exit(1)
    
    console.rule(f"[bold blue]SEO Audit Explanation[/] [white]{data.get('site', 'Unknown Site')}[/]")
    
    # Basic stats
    stats_table = Table(title="Audit Overview")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="white")
    stats_table.add_row("Site", data.get('site', 'Unknown'))
    stats_table.add_row("Pages Scanned", str(data.get('pages_scanned', 0)))
    stats_table.add_row("Issues Found", str(len(data.get('issues', []))))
    stats_table.add_row("Audit Date", data.get('meta', {}).get('timestamp', 'Unknown'))
    console.print(stats_table)
    
    # Issues explanation
    issues = data.get('issues', [])
    if not issues:
        console.print("[green]✓ No SEO issues found![/]")
        return
    
    # Group issues by type and severity
    issues_by_type = {}
    severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
    
    for issue in issues:
        issue_type = issue['type']
        severity = issue['severity']
        
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)
        severity_counts[severity] += 1
    
    # Severity summary
    severity_table = Table(title="Issues by Severity")
    severity_table.add_column("Severity", style="red")
    severity_table.add_column("Count", style="white")
    for severity, count in severity_counts.items():
        if count > 0:
            color = {"high": "red", "medium": "yellow", "low": "blue", "info": "dim"}[severity]
            severity_table.add_row(severity, f"[{color}]{count}[/{color}]")
    console.print(severity_table)
    
    # Detailed issues explanation
    console.print("\n[bold]Issues Found:[/]")
    for issue_type, type_issues in issues_by_type.items():
        console.print(f"\n[bold magenta]{issue_type.replace('_', ' ').title()}[/] ({len(type_issues)} instances)")
        
        # Provide basic explanation for each issue type
        explanations = {
            "title_missing": "Each page should have a unique title tag that accurately describes its content",
            "title_too_long": "Title tags should ideally be under 60 characters for optimal display in search results",
            "meta_description_missing": "Meta descriptions help users understand your page in search results and can improve click-through rates",
            "noindex": "This page is blocked from search engine indexing with a noindex directive",
            "http_error": "The page returned an HTTP error code, indicating it may be inaccessible",
            "fetch_error": "The page could not be fetched, possibly due to network issues or server problems",
            "duplicate_title": "Multiple pages have the same title, which can confuse search engines about which page is more relevant",
            "broken_link": "Links that lead to non-existent pages create poor user experience and can harm SEO",
        }
        
        explanation = explanations.get(issue_type, "This is a SEO issue that may affect your site's performance")
        console.print(f"[dim]• {explanation}[/]")
        
        # Show affected URLs
        for issue in type_issues[:3]:  # Limit to first 3 to avoid clutter
            console.print(f"  • {issue['url']}")
            if issue.get('detail'):
                console.print(f"    [dim]Details: {issue['detail']}[/]")
        
        if len(type_issues) > 3:
            console.print(f"  [dim]... and {len(type_issues) - 3} more[/]")
    
    # AI explanation if requested
    if use_ai:
        try:
            # Import here to avoid circular imports
            import os
            from dotenv import load_dotenv
            
            # Load .env - check multiple possible locations
            import sys
            possible_paths = [
                # Current working directory (most common when running from project root)
                os.path.join(os.getcwd(), ".env"),
                # Project root relative to this file
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
            ]
            
            env_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    env_path = path
                    break
            
            if env_path:
                load_dotenv(env_path)
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                console.print("\n[yellow]AI explanation requested but OPENAI_API_KEY not found.[/]")
                console.print("Add your API key to .env file to use AI explanations.")
                return
            
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            console.print("\n[bold]🤖 AI-Powered Analysis:[/]")
            console.print("[dim]Generating detailed insights...[/]")
            
            # Prepare prompt for AI
            issues_summary = json.dumps(issues, indent=2)
            prompt = f"""
            Analyze these SEO audit results for website {data.get('site')} and provide actionable recommendations:
            
            {issues_summary}
            
            Please provide:
            1. Priority ranking of issues (which to fix first)
            2. Specific actionable steps for each issue type
            3. Expected impact on SEO if these issues are fixed
            4. Quick wins vs long-term improvements
            
            Be concise and practical.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an SEO expert providing actionable advice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            
            ai_response = response.choices[0].message.content or ""
            console.print(f"[cyan]{ai_response}[/]")
            
        except ImportError:
            console.print("\n[yellow]OpenAI library not installed. Install with: pip install openai[/]")
        except Exception as e:
            console.print(f"\n[red]Error generating AI explanation: {str(e)}[/]")


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
from .ai.summarizer import summarize_with_ai
from pydantic import ValidationError

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
from .reporting.excel import write_xlsx
from .reporting.pdf import write_pdf
from .ai.summarizer import summarize_with_ai

@app.command()
def report(
    folder: Path = typer.Argument(..., help="Folder containing summary.json"),
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

    summary_path = folder / "summary.json"
    if not summary_path.exists():
        console.print(f"[red]Missing:[/] {summary_path}")
        raise typer.Exit(code=2)

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
