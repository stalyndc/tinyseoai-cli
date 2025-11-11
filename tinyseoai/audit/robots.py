"""
Robots.txt parsing and sitemap discovery.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from loguru import logger


class RobotsAnalyzer:
    """Analyze robots.txt files and discover sitemaps."""

    def __init__(self, base_url: str):
        """
        Initialize the robots analyzer.

        Args:
            base_url: The base URL of the website
        """
        self.base_url = base_url
        parsed = urlparse(base_url)
        self.robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        self.parser = RobotFileParser()
        self.parser.set_url(self.robots_url)
        self.content: str | None = None
        self.sitemaps: list[str] = []
        self.crawl_delay: float | None = None
        self.disallowed_paths: list[str] = []
        self.allowed_paths: list[str] = []

    async def fetch_and_parse(self, client: httpx.AsyncClient) -> bool:
        """
        Fetch and parse the robots.txt file.

        Args:
            client: HTTP client to use for fetching

        Returns:
            True if robots.txt was found and parsed successfully, False otherwise
        """
        try:
            response = await client.get(self.robots_url, timeout=10.0)
            if response.status_code == 200:
                self.content = response.text
                self.parser.parse(self.content.splitlines())
                self._extract_sitemaps()
                self._extract_crawl_delay()
                self._extract_rules()
                logger.info(f"Successfully parsed robots.txt from {self.robots_url}")
                return True
            elif response.status_code == 404:
                logger.info(f"No robots.txt found at {self.robots_url}")
                return False
            else:
                logger.warning(
                    f"Unexpected status code {response.status_code} for robots.txt"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to fetch robots.txt: {e}")
            return False

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if a URL can be fetched according to robots.txt.

        Args:
            url: URL to check
            user_agent: User agent to check for

        Returns:
            True if URL can be fetched, False otherwise
        """
        if not self.content:
            # No robots.txt means everything is allowed
            return True

        return self.parser.can_fetch(user_agent, url)

    def _extract_sitemaps(self) -> None:
        """Extract sitemap URLs from robots.txt content."""
        if not self.content:
            return

        sitemap_pattern = re.compile(r"^\s*Sitemap:\s*(.+)\s*$", re.IGNORECASE | re.MULTILINE)
        matches = sitemap_pattern.findall(self.content)
        self.sitemaps = [match.strip() for match in matches]

        logger.info(f"Found {len(self.sitemaps)} sitemap(s) in robots.txt")

    def _extract_crawl_delay(self) -> None:
        """Extract crawl delay directive from robots.txt."""
        if not self.content:
            return

        # Look for Crawl-delay directive
        delay_pattern = re.compile(
            r"^\s*Crawl-delay:\s*(\d+(?:\.\d+)?)\s*$", re.IGNORECASE | re.MULTILINE
        )
        match = delay_pattern.search(self.content)
        if match:
            self.crawl_delay = float(match.group(1))
            logger.info(f"Crawl delay specified: {self.crawl_delay} seconds")

    def _extract_rules(self) -> None:
        """Extract disallow and allow rules from robots.txt."""
        if not self.content:
            return

        # Extract Disallow rules
        disallow_pattern = re.compile(
            r"^\s*Disallow:\s*(.+)\s*$", re.IGNORECASE | re.MULTILINE
        )
        self.disallowed_paths = [
            match.strip() for match in disallow_pattern.findall(self.content)
        ]

        # Extract Allow rules
        allow_pattern = re.compile(r"^\s*Allow:\s*(.+)\s*$", re.IGNORECASE | re.MULTILINE)
        self.allowed_paths = [match.strip() for match in allow_pattern.findall(self.content)]

    def get_sitemap_urls(self) -> list[str]:
        """
        Get all sitemap URLs discovered.

        Returns:
            List of sitemap URLs
        """
        return self.sitemaps

    def get_summary(self) -> dict:
        """
        Get a summary of robots.txt analysis.

        Returns:
            Dictionary with robots.txt summary
        """
        return {
            "robots_url": self.robots_url,
            "exists": self.content is not None,
            "sitemaps_count": len(self.sitemaps),
            "sitemaps": self.sitemaps,
            "crawl_delay": self.crawl_delay,
            "disallowed_paths_count": len(self.disallowed_paths),
            "allowed_paths_count": len(self.allowed_paths),
            "disallowed_paths": self.disallowed_paths[:10],  # Limit for summary
            "allowed_paths": self.allowed_paths[:10],
        }


class SitemapParser:
    """Parse XML sitemaps and discover URLs."""

    def __init__(self, sitemap_url: str):
        """
        Initialize the sitemap parser.

        Args:
            sitemap_url: URL of the sitemap
        """
        self.sitemap_url = sitemap_url
        self.urls: list[dict] = []
        self.nested_sitemaps: list[str] = []

    async def fetch_and_parse(self, client: httpx.AsyncClient) -> bool:
        """
        Fetch and parse the sitemap.

        Args:
            client: HTTP client to use for fetching

        Returns:
            True if sitemap was parsed successfully, False otherwise
        """
        try:
            response = await client.get(self.sitemap_url, timeout=15.0)
            if response.status_code != 200:
                logger.warning(
                    f"Failed to fetch sitemap {self.sitemap_url}: {response.status_code}"
                )
                return False

            content = response.text
            self._parse_xml(content)
            logger.info(
                f"Parsed sitemap {self.sitemap_url}: {len(self.urls)} URLs, "
                f"{len(self.nested_sitemaps)} nested sitemaps"
            )
            return True

        except Exception as e:
            logger.error(f"Error parsing sitemap {self.sitemap_url}: {e}")
            return False

    def _parse_xml(self, content: str) -> None:
        """
        Parse sitemap XML content.

        Args:
            content: XML content to parse
        """
        # Check if this is a sitemap index
        if "<sitemapindex" in content:
            self._parse_sitemap_index(content)
        else:
            self._parse_urlset(content)

    def _parse_sitemap_index(self, content: str) -> None:
        """Parse sitemap index to find nested sitemaps."""
        # Extract sitemap locations
        loc_pattern = re.compile(r"<sitemap>.*?<loc>(.*?)</loc>.*?</sitemap>", re.DOTALL)
        matches = loc_pattern.findall(content)
        self.nested_sitemaps = [match.strip() for match in matches]

    def _parse_urlset(self, content: str) -> None:
        """Parse urlset to extract URLs and metadata."""
        # Extract URL entries
        url_pattern = re.compile(r"<url>(.*?)</url>", re.DOTALL)
        url_entries = url_pattern.findall(content)

        for entry in url_entries:
            url_data = self._extract_url_data(entry)
            if url_data:
                self.urls.append(url_data)

    def _extract_url_data(self, entry: str) -> dict | None:
        """Extract data from a single URL entry."""
        # Extract loc (required)
        loc_match = re.search(r"<loc>(.*?)</loc>", entry)
        if not loc_match:
            return None

        url = loc_match.group(1).strip()

        # Extract optional fields
        lastmod_match = re.search(r"<lastmod>(.*?)</lastmod>", entry)
        changefreq_match = re.search(r"<changefreq>(.*?)</changefreq>", entry)
        priority_match = re.search(r"<priority>(.*?)</priority>", entry)

        return {
            "loc": url,
            "lastmod": lastmod_match.group(1).strip() if lastmod_match else None,
            "changefreq": changefreq_match.group(1).strip() if changefreq_match else None,
            "priority": float(priority_match.group(1).strip())
            if priority_match
            else None,
        }

    def get_urls(self) -> list[str]:
        """
        Get all URLs from the sitemap.

        Returns:
            List of URL strings
        """
        return [url_data["loc"] for url_data in self.urls]

    def get_priority_urls(self, min_priority: float = 0.8) -> list[str]:
        """
        Get high-priority URLs from the sitemap.

        Args:
            min_priority: Minimum priority threshold

        Returns:
            List of high-priority URLs
        """
        return [
            url_data["loc"]
            for url_data in self.urls
            if url_data.get("priority") and url_data["priority"] >= min_priority
        ]

    def get_nested_sitemaps(self) -> list[str]:
        """
        Get nested sitemap URLs.

        Returns:
            List of nested sitemap URLs
        """
        return self.nested_sitemaps


async def discover_sitemaps(
    base_url: str, client: httpx.AsyncClient, max_depth: int = 2
) -> list[str]:
    """
    Discover all sitemaps for a website.

    Args:
        base_url: Base URL of the website
        client: HTTP client to use
        max_depth: Maximum depth to follow nested sitemaps

    Returns:
        List of all discovered URLs from sitemaps
    """
    # First, check robots.txt for sitemaps
    robots = RobotsAnalyzer(base_url)
    await robots.fetch_and_parse(client)

    sitemap_urls = robots.get_sitemap_urls()

    # If no sitemaps in robots.txt, try common locations
    if not sitemap_urls:
        parsed = urlparse(base_url)
        common_sitemap_urls = [
            f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
            f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
            f"{parsed.scheme}://{parsed.netloc}/sitemap-index.xml",
        ]
        sitemap_urls = common_sitemap_urls

    # Parse all sitemaps
    all_urls: list[str] = []
    processed_sitemaps = set()

    async def parse_sitemap(url: str, depth: int = 0):
        if depth > max_depth or url in processed_sitemaps:
            return

        processed_sitemaps.add(url)
        parser = SitemapParser(url)
        success = await parser.fetch_and_parse(client)

        if success:
            all_urls.extend(parser.get_urls())

            # Recursively parse nested sitemaps
            if depth < max_depth:
                for nested in parser.get_nested_sitemaps():
                    await parse_sitemap(nested, depth + 1)

    # Parse all discovered sitemaps
    for sitemap_url in sitemap_urls:
        await parse_sitemap(sitemap_url)

    logger.info(f"Discovered {len(all_urls)} URLs from {len(processed_sitemaps)} sitemap(s)")
    return all_urls
