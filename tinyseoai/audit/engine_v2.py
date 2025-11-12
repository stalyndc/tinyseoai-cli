# Copyright (c) 2025 Stalyn Disla
# Licensed under the MIT License

"""
Enhanced SEO audit engine integrating all check modules.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from urllib.parse import urlparse

import httpx
from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..data.models import AuditResult, Issue
from ..data.scoring import HealthScoreCalculator, prioritize_issues
from ..utils.url import normalize_url, same_host
from .checks.content import ContentAnalyzer, DuplicateContentDetector
from .checks.indexability import IndexabilityChecker, check_pagination
from .checks.links import LinkChecker
from .checks.meta import MetaTagChecker
from .checks.performance import PerformanceChecker
from .checks.security import SecurityChecker, check_ssl_certificate
from .crawler import extract_links, extract_meta, fetch_page
from .parser import HTMLParser
from .robots import RobotsAnalyzer, discover_sitemaps

# Constants
DEFAULT_MAX_PAGES = 50
USER_AGENT = "TinySEOAI/0.2 (+https://tinyseoai.com; cli) python-httpx"


class _DummyProgress:
    """Dummy progress context manager for when progress is disabled."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def add_task(self, *args, **kwargs):
        return None

    def update(self, *args, **kwargs):
        pass

    def advance(self, *args, **kwargs):
        pass


class EnhancedPage:
    """Enhanced page representation with full analysis data."""

    def __init__(
        self,
        url: str,
        status: int = 0,
        title: str | None = None,
        meta_desc: str | None = None,
        noindex: bool = False,
        html: str = "",
        headers: dict = None,
    ):
        self.url = url
        self.status = status
        self.title = title
        self.meta_desc = meta_desc
        self.noindex = noindex
        self.html = html
        self.headers = headers or {}
        self.links: set[str] = set()
        self.internal_links: list[dict] = []
        self.external_links: list[dict] = []


async def comprehensive_audit(
    seed_url: str,
    max_pages: int = DEFAULT_MAX_PAGES,
    enable_all_checks: bool = True,
    show_progress: bool = True
) -> AuditResult:
    """
    Comprehensive SEO audit using all available check modules.

    Args:
        seed_url: Starting URL to audit
        max_pages: Maximum pages to crawl
        enable_all_checks: If False, only run basic checks (faster)
        show_progress: If True, display progress bar during crawl

    Returns:
        Enhanced AuditResult with all findings and scores
    """
    logger.info(f"Starting comprehensive audit of {seed_url}")
    seed_url = normalize_url(seed_url)
    origin = urlparse(seed_url)
    host = origin.netloc
    site_root = f"{origin.scheme}://{origin.netloc}"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }

    all_issues: list[Issue] = []
    pages: list[EnhancedPage] = []

    # Phase 1: Analyze robots.txt
    logger.info("Phase 1: Analyzing robots.txt...")
    robots_analyzer = RobotsAnalyzer(site_root)

    async with httpx.AsyncClient(headers=headers, http2=True) as client:
        robots_exists = await robots_analyzer.fetch_and_parse(client)

        if not robots_exists:
            all_issues.append(
                Issue(
                    url=f"{site_root}/robots.txt",
                    type="robots_missing",
                    severity="low",
                    detail="No robots.txt found",
                )
            )

        # Discover sitemaps if enabled
        sitemap_urls = []
        if enable_all_checks:
            logger.info("Discovering sitemaps...")
            sitemap_urls = await discover_sitemaps(site_root, client, max_depth=1)
            logger.info(f"Found {len(sitemap_urls)} URLs in sitemaps")

        # Phase 2: Crawl pages
        logger.info(f"Phase 2: Crawling up to {max_pages} pages...")
        visited: set[str] = set()
        to_visit: deque[str] = deque([seed_url])

        # Prioritize sitemap URLs if available
        if sitemap_urls:
            # Add high-priority sitemap URLs to the front of the queue
            for sitemap_url in sitemap_urls[:max_pages]:
                if sitemap_url not in to_visit:
                    to_visit.append(sitemap_url)

        crawl_count = 0

        # Create progress bar context (or dummy context if disabled)
        progress_context = (
            Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("[cyan]{task.fields[current_url]}"),
            )
            if show_progress
            else _DummyProgress()
        )

        with progress_context as progress:
            crawl_task = progress.add_task(
                "[cyan]Crawling pages...",
                total=max_pages,
                current_url=""
            ) if show_progress else None

            while to_visit and crawl_count < max_pages:
                url = to_visit.popleft()
                if url in visited:
                    continue
                visited.add(url)

                # Check robots.txt permission
                if robots_exists and not robots_analyzer.can_fetch(url):
                    logger.debug(f"Skipping {url} (disallowed by robots.txt)")
                    continue

                # Update progress bar with current URL
                if show_progress:
                    short_url = url if len(url) <= 50 else url[:47] + "..."
                    progress.update(crawl_task, current_url=short_url)

                # Fetch page
                resp = await fetch_page(client, url)
                if resp is None:
                    all_issues.append(
                        Issue(url=url, type="fetch_error", severity="high", detail="Request failed")
                    )
                    if show_progress:
                        progress.advance(crawl_task)
                    crawl_count += 1
                    continue

                status = resp.status_code
                response_headers = dict(resp.headers)
                html = (
                    resp.text
                    if resp.headers.get("content-type", "").startswith("text/html")
                    else ""
                )

                page = EnhancedPage(
                    url=url, status=status, html=html, headers=response_headers
                )

                # Check for HTTP errors
                if status >= 400:
                    all_issues.append(
                        Issue(url=url, type="http_error", severity="high", detail=f"Status {status}")
                    )
                else:
                    # Extract basic metadata
                    title, meta_desc, noindex = extract_meta(html)
                    page.title = title
                    page.meta_desc = meta_desc
                    page.noindex = noindex

                    # Run comprehensive checks on this page
                    page_issues = await _run_page_checks(
                        page, site_root, enable_all_checks, client
                    )
                    all_issues.extend(page_issues)

                    # Extract links for crawling
                    # BUGFIX: Cap queue size to prevent unbounded memory growth
                    # See: BUGFIXES.md #6
                    links = extract_links(html, url)
                    for link in links:
                        if same_host(link, host):
                            page.links.add(link)
                            # Only add to queue if we haven't visited and queue isn't full
                            if link not in visited and len(to_visit) < max_pages:
                                to_visit.append(link)

                pages.append(page)
                crawl_count += 1

                # Update progress bar
                if show_progress:
                    progress.advance(crawl_task)
                elif crawl_count % 10 == 0:
                    # Keep old logging behavior when progress is disabled
                    logger.info(f"Crawled {crawl_count}/{max_pages} pages...")

    logger.info("Phase 3: Running post-crawl analysis...")

    # Phase 3: Post-crawl checks
    post_crawl_issues = await _run_post_crawl_checks(pages, seed_url, enable_all_checks)
    all_issues.extend(post_crawl_issues)

    # Phase 4: Calculate scores
    logger.info("Phase 4: Calculating health scores...")
    health_calc = HealthScoreCalculator()
    health_score = health_calc.calculate_health_score(all_issues, len(pages))

    # Prioritize issues
    prioritize_issues(all_issues)

    # Build enhanced metadata
    meta = {
        "max_pages": max_pages,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": "tinyseoai/0.2.0",
        "robots_txt_exists": robots_analyzer.content is not None,
        "sitemaps_found": len(robots_analyzer.get_sitemap_urls()),
        "crawl_delay": robots_analyzer.crawl_delay,
        "total_sitemap_urls": len(sitemap_urls) if sitemap_urls else 0,
        "health_score": health_score["overall_score"],
        "health_grade": health_score["grade"],
        "category_scores": health_score.get("category_scores", {}),
        "top_recommendations": health_score.get("recommendations", [])[:5],
    }

    logger.info(
        f"Audit complete: {len(pages)} pages, {len(all_issues)} issues, "
        f"health score: {health_score['overall_score']}/100 ({health_score['grade']})"
    )

    return AuditResult(
        site=seed_url, pages_scanned=len(pages), issues=all_issues, meta=meta
    )


async def _run_page_checks(
    page: EnhancedPage, site_root: str, enable_all: bool, client: httpx.AsyncClient
) -> list[Issue]:
    """Run all checks for a single page."""
    issues = []

    # Basic checks (always run)
    issues.extend(_check_title(page.url, page.title))
    issues.extend(_check_meta_description(page.url, page.meta_desc))
    issues.extend(_check_noindex(page.url, page.noindex))

    if not enable_all or not page.html:
        return issues

    # Enhanced checks
    try:
        # Security checks
        security_checker = SecurityChecker(page.url)
        sec_issues = await security_checker.check_all(client)
        issues.extend(sec_issues)

        # SSL certificate check (only for HTTPS)
        if page.url.startswith("https://"):
            ssl_issues = await check_ssl_certificate(page.url)
            issues.extend(ssl_issues)

    except Exception as e:
        logger.warning(f"Security checks failed for {page.url}: {e}")

    try:
        # Meta tag checks
        meta_checker = MetaTagChecker(page.html, page.url)
        meta_issues = meta_checker.check_all()
        issues.extend(meta_issues)
    except Exception as e:
        logger.warning(f"Meta tag checks failed for {page.url}: {e}")

    try:
        # Indexability checks
        index_checker = IndexabilityChecker(page.html, page.url)
        index_issues = index_checker.check_all()
        issues.extend(index_issues)

        # Pagination checks
        pagination_issues = check_pagination(page.html, page.url)
        issues.extend(pagination_issues)
    except Exception as e:
        logger.warning(f"Indexability checks failed for {page.url}: {e}")

    try:
        # Content quality checks
        content_analyzer = ContentAnalyzer(page.html, page.url)
        content_issues = content_analyzer.check_all()
        issues.extend(content_issues)
    except Exception as e:
        logger.warning(f"Content checks failed for {page.url}: {e}")

    try:
        # Performance checks
        perf_checker = PerformanceChecker(page.html, page.url, page.headers)
        perf_issues = perf_checker.check_all()
        issues.extend(perf_issues)
    except Exception as e:
        logger.warning(f"Performance checks failed for {page.url}: {e}")

    return issues


async def _run_post_crawl_checks(
    pages: list[EnhancedPage], seed_url: str, enable_all: bool
) -> list[Issue]:
    """Run checks that require analysis across all pages."""
    issues = []

    # Duplicate title/description checks (always run)
    issues.extend(_check_duplicate_titles(pages))
    issues.extend(_check_duplicate_meta_descriptions(pages))

    if not enable_all:
        return issues

    try:
        # Duplicate content detection
        dup_detector = DuplicateContentDetector()
        for page in pages:
            if page.html:
                content_analyzer = ContentAnalyzer(page.html, page.url)
                text = content_analyzer.text
                dup_detector.add_page(page.url, text)

        # Find exact duplicates
        dup_issues = dup_detector.find_duplicates()
        issues.extend(dup_issues)

        # Find near-duplicates (may be slow for many pages)
        if len(pages) < 100:  # Only for smaller sites
            near_dup_issues = dup_detector.find_near_duplicates(threshold=0.8)
            issues.extend(near_dup_issues)

    except Exception as e:
        logger.warning(f"Duplicate content detection failed: {e}")

    try:
        # Link graph analysis
        link_checker = LinkChecker(seed_url)

        # Build page data for link analysis
        pages_data = []
        for page in pages:
            if page.html:
                parser = HTMLParser(page.html, page.url)
                page.internal_links = parser.content_parser.extract_internal_links(seed_url)
                page.external_links = parser.content_parser.extract_external_links(seed_url)

                pages_data.append({
                    "url": page.url,
                    "internal_links": page.internal_links,
                    "external_links": page.external_links,
                })

        # Analyze internal linking
        link_issues = link_checker.analyze_internal_linking(pages_data)
        issues.extend(link_issues)

    except Exception as e:
        logger.warning(f"Link analysis failed: {e}")

    return issues


def _check_title(url: str, title: str | None) -> list[Issue]:
    """Check title tag."""
    issues = []
    if not title:
        issues.append(Issue(url=url, type="title_missing", severity="medium"))
    elif len(title) > 60:
        issues.append(
            Issue(url=url, type="title_too_long", severity="low", detail=str(len(title)))
        )
    return issues


def _check_meta_description(url: str, meta_desc: str | None) -> list[Issue]:
    """Check meta description."""
    issues = []
    if not meta_desc:
        issues.append(Issue(url=url, type="meta_description_missing", severity="low"))
    return issues


def _check_noindex(url: str, noindex: bool) -> list[Issue]:
    """Check noindex directive."""
    issues = []
    if noindex:
        issues.append(Issue(url=url, type="noindex", severity="info"))
    return issues


def _check_duplicate_titles(pages: list[EnhancedPage]) -> list[Issue]:
    """Check for duplicate titles."""
    issues = []
    titles: dict[str, list[str]] = {}

    for page in pages:
        if page.title:
            key = page.title.strip().lower()
            titles.setdefault(key, []).append(page.url)

    for title_text, urls in titles.items():
        if len(urls) > 1:
            for url in urls:
                issues.append(
                    Issue(url=url, type="duplicate_title", severity="low", detail=title_text[:80])
                )

    return issues


def _check_duplicate_meta_descriptions(pages: list[EnhancedPage]) -> list[Issue]:
    """Check for duplicate meta descriptions."""
    issues = []
    descriptions: dict[str, list[str]] = {}

    for page in pages:
        if page.meta_desc:
            key = page.meta_desc.strip().lower()
            descriptions.setdefault(key, []).append(page.url)

    for desc_text, urls in descriptions.items():
        if len(urls) > 1:
            for url in urls:
                issues.append(
                    Issue(
                        url=url,
                        type="duplicate_meta_description",
                        severity="low",
                        detail=desc_text[:120],
                    )
                )

    return issues
