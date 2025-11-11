"""
Core SEO audit engine that coordinates crawling and checks.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Set
from urllib.parse import urlparse

import httpx

from ..data.models import Issue, AuditResult
from ..utils.url import normalize_url, same_host
from .crawler import fetch_page, extract_meta, extract_links
from bs4 import BeautifulSoup

# Constants
DEFAULT_MAX_PAGES = 50
USER_AGENT = (
    "TinySEOAI/0.1 (+https://tinyseoai.com; cli) "
    "python-httpx"
)


class Page:
    """Represents a crawled page with its metadata."""

    def __init__(
        self,
        url: str,
        status: int = 0,
        title: str | None = None,
        meta_desc: str | None = None,
        noindex: bool = False,
        links: Set[str] | None = None,
    ):
        self.url = url
        self.status = status
        self.title = title
        self.meta_desc = meta_desc
        self.noindex = noindex
        self.links = links if links is not None else set()


async def audit_site(seed_url: str, max_pages: int = DEFAULT_MAX_PAGES) -> AuditResult:
    """
    Main audit engine that crawls a website and performs SEO checks.

    Args:
        seed_url: The starting URL to audit
        max_pages: Maximum number of pages to crawl

    Returns:
        AuditResult containing all findings and metadata
    """
    seed_url = normalize_url(seed_url)
    origin = urlparse(seed_url)
    host = origin.netloc

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"
    }

    visited: Set[str] = set()
    to_visit: deque[str] = deque([seed_url])
    pages: list[Page] = []
    issues: list[Issue] = []

    # --- robots.txt & sitemap checks (best-effort) ---
    # BUGFIX: Use specific exception handling (See: BUGFIXES.md #4)
    site_root = f"{origin.scheme}://{origin.netloc}"
    try:
        rob = await httpx.AsyncClient(headers=headers, http2=True).get(f"{site_root}/robots.txt", timeout=10.0)
        if rob.status_code >= 400:
            issues.append(Issue(url=site_root + "/robots.txt", type="robots_missing", severity="low"))
        else:
            # parse simple "Sitemap:" lines
            text = rob.text.lower()
            has_sitemap_hint = "sitemap:" in text
            if not has_sitemap_hint:
                # also check direct /sitemap.xml
                sm = await httpx.AsyncClient(headers=headers, http2=True).get(f"{site_root}/sitemap.xml", timeout=10.0, follow_redirects=True)
                if sm.status_code >= 400:
                    issues.append(Issue(url=site_root + "/sitemap.xml", type="sitemap_missing", severity="low"))
    except (httpx.HTTPError, httpx.TimeoutException, OSError) as e:
        # Network errors are expected for some sites
        issues.append(Issue(url=site_root + "/robots.txt", type="robots_check_error", severity="low", detail=str(e)[:100]))

    async with httpx.AsyncClient(headers=headers, http2=True) as client:
        while to_visit and len(pages) < max_pages:
            url = to_visit.popleft()
            if url in visited:
                continue
            visited.add(url)

            # Fetch the page
            resp = await fetch_page(client, url)
            if resp is None:
                issues.append(
                    Issue(url=url, type="fetch_error", severity="high", detail="Request failed")
                )
                continue

            status = resp.status_code
            html = resp.text if resp.headers.get("content-type", "").startswith("text/html") else ""

            page = Page(url=url, status=status, links=set())

            # Check for HTTP errors
            if status >= 400:
                issues.append(
                    Issue(url=url, type="http_error", severity="high", detail=f"Status {status}")
                )
            else:
                # Extract metadata
                title, meta_desc, noindex = extract_meta(html)
                page.title = title
                page.meta_desc = meta_desc
                page.noindex = noindex

                # Image alt checks (missing or empty)
                try:
                    soup = BeautifulSoup(html, "lxml")
                    for img in soup.find_all("img"):
                        alt = (img.get("alt") or "").strip()
                        src = (img.get("src") or "").strip()
                        if alt == "":
                            issues.append(Issue(url=url, type="img_alt_missing", severity="low", detail=src[:120]))
                except Exception:
                    pass

                # Run basic SEO checks
                issues.extend(_check_title(url, title))
                issues.extend(_check_meta_description(url, meta_desc))
                issues.extend(_check_noindex(url, noindex))

                # Extract and queue internal links
                # BUGFIX: Cap queue size to prevent unbounded memory growth
                # See: BUGFIXES.md #6
                links = extract_links(html, url)
                page.links = set()
                for link in links:
                    if same_host(link, host):
                        page.links.add(link)
                        # Only add to queue if we haven't visited and queue isn't full
                        if link not in visited and len(to_visit) < max_pages:
                            to_visit.append(link)

                # Quick broken-link check for internal links (sampled)
                broken_link_issues = await _check_broken_links(client, url, list(page.links)[:10])
                issues.extend(broken_link_issues)

            pages.append(page)

    # Post-crawl checks
    issues.extend(_check_duplicate_titles(pages))
    issues.extend(_check_duplicate_meta_descriptions(pages))

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


def _check_title(url: str, title: str | None) -> list[Issue]:
    """Check title tag for common issues."""
    issues = []

    if not title:
        issues.append(Issue(url=url, type="title_missing", severity="medium"))
    elif len(title) > 60:
        issues.append(
            Issue(url=url, type="title_too_long", severity="low", detail=str(len(title)))
        )

    return issues


def _check_meta_description(url: str, meta_desc: str | None) -> list[Issue]:
    """Check meta description presence."""
    issues = []

    if not meta_desc:
        issues.append(Issue(url=url, type="meta_description_missing", severity="low"))

    return issues


def _check_noindex(url: str, noindex: bool) -> list[Issue]:
    """Check for noindex directive."""
    issues = []

    if noindex:
        issues.append(Issue(url=url, type="noindex", severity="info"))

    return issues


async def _check_broken_links(
    client: httpx.AsyncClient, page_url: str, links: list[str]
) -> list[Issue]:
    """Check a sample of links for broken status."""
    issues = []

    for link in links:
        try:
            r = await client.head(link, timeout=10.0, follow_redirects=True)
            if r.status_code >= 400:
                issues.append(
                    Issue(url=page_url, type="broken_link", severity="medium", detail=link)
                )
        except Exception:
            issues.append(
                Issue(url=page_url, type="broken_link", severity="medium", detail=link)
            )

    return issues


def _check_duplicate_titles(pages: list[Page]) -> list[Issue]:
    """Check for duplicate title tags across pages."""
    issues = []
    titles: dict[str, list[str]] = {}

    for page in pages:
        if page.title:
            normalized_title = page.title.strip().lower()
            titles.setdefault(normalized_title, []).append(page.url)

    for title_text, urls in titles.items():
        if len(urls) > 1:
            for url in urls:
                issues.append(
                    Issue(url=url, type="duplicate_title", severity="low", detail=title_text[:80])
                )

    return issues


def _check_duplicate_meta_descriptions(pages: list[Page]) -> list[Issue]:
    """Check for duplicate meta descriptions across pages."""
    issues = []
    mds: dict[str, list[str]] = {}
    
    for page in pages:
        if page.meta_desc:
            key = page.meta_desc.strip().lower()
            if key:
                mds.setdefault(key, []).append(page.url)
    
    for desc, urls in mds.items():
        if len(urls) > 1:
            for url in urls:
                issues.append(
                    Issue(
                        url=url, 
                        type="duplicate_meta_description", 
                        severity="low", 
                        detail=(desc[:120] + ("…" if len(desc) > 120 else ""))
                    )
                )
    
    return issues
