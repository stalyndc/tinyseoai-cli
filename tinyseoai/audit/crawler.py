"""
Web crawler functionality for fetching and extracting page data.
"""
from __future__ import annotations

import re
from typing import Set, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..utils.url import normalize_url


async def fetch_page(
    client: httpx.AsyncClient, url: str
) -> httpx.Response | None:
    """
    Fetch a single page asynchronously.

    BUGFIX: Improved exception handling with better timeouts and logging.
    See: BUGFIXES.md #4

    Args:
        client: HTTP client to use for the request
        url: URL to fetch

    Returns:
        Response object or None if fetch failed
    """
    try:
        # BUGFIX: Use separate connect/read timeouts and limit redirects
        timeout = httpx.Timeout(10.0, connect=5.0)
        response = await client.get(
            url,
            timeout=timeout,
            follow_redirects=True,
        )
        return response
    except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout):
        # Timeout is expected, don't log noise
        return None
    except httpx.HTTPError as e:
        # Log HTTP-specific errors
        from loguru import logger
        logger.debug(f"HTTP error fetching {url}: {e}")
        return None
    except Exception as e:
        # Unexpected errors should be logged
        from loguru import logger
        logger.warning(f"Unexpected error fetching {url}: {type(e).__name__}: {e}")
        return None


def extract_links(html: str, base: str) -> Set[str]:
    """
    Extract all links from HTML content.

    Args:
        html: HTML content to parse
        base: Base URL for resolving relative links

    Returns:
        Set of normalized absolute URLs
    """
    soup = BeautifulSoup(html, "lxml")
    links: Set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href").strip()

        # Skip fragment-only and javascript: links
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        # Convert to absolute URL and normalize
        absolute_url = urljoin(base, href)
        links.add(normalize_url(absolute_url))

    return links


def extract_meta(html: str) -> Tuple[str | None, str | None, bool]:
    """
    Extract key metadata from HTML: title, meta description, and noindex status.

    Args:
        html: HTML content to parse

    Returns:
        Tuple of (title, meta_description, noindex_flag)
    """
    soup = BeautifulSoup(html, "lxml")

    # Extract title
    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Extract meta description
    meta_desc = None
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    # Check for noindex directive
    noindex = False
    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots_tag and robots_tag.get("content"):
        content = robots_tag["content"].lower()
        if "noindex" in content:
            noindex = True

    return title, meta_desc, noindex
