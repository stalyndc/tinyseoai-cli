"""
Indexability checks including canonical tags, robots meta, and XML sitemap validation.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ...data.models import Issue


class IndexabilityChecker:
    """Check indexability-related SEO factors."""

    def __init__(self, html: str, url: str):
        """
        Initialize the indexability checker.

        Args:
            html: HTML content to check
            url: URL of the page
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, "lxml")
        self.parsed_url = urlparse(url)

    def check_all(self) -> list[Issue]:
        """
        Run all indexability checks.

        Returns:
            List of indexability issues
        """
        issues = []

        issues.extend(self.check_canonical())
        issues.extend(self.check_robots_meta())
        issues.extend(self.check_meta_robots())
        issues.extend(self.check_x_robots_tag())

        return issues

    def check_canonical(self) -> list[Issue]:
        """
        Check canonical tag implementation.

        Returns:
            List of canonical tag issues
        """
        issues = []

        # Find all canonical tags
        canonical_tags = self.soup.find_all("link", rel="canonical")

        if len(canonical_tags) == 0:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_canonical",
                    severity="medium",
                    detail="No canonical tag found. This can cause duplicate content issues.",
                )
            )
        elif len(canonical_tags) > 1:
            issues.append(
                Issue(
                    url=self.url,
                    type="multiple_canonical_tags",
                    severity="high",
                    detail=f"Multiple canonical tags found ({len(canonical_tags)}). "
                    "Only one canonical tag should be present.",
                )
            )
        else:
            canonical_tag = canonical_tags[0]
            canonical_url = canonical_tag.get("href")

            if not canonical_url:
                issues.append(
                    Issue(
                        url=self.url,
                        type="empty_canonical",
                        severity="high",
                        detail="Canonical tag is empty",
                    )
                )
            else:
                # Make canonical absolute if relative
                canonical_url = urljoin(self.url, canonical_url)

                # Check if canonical is absolute
                if not canonical_url.startswith(("http://", "https://")):
                    issues.append(
                        Issue(
                            url=self.url,
                            type="canonical_not_absolute",
                            severity="medium",
                            detail="Canonical URL should be absolute (include full URL)",
                        )
                    )

                # Check if canonical points to itself (recommended)
                current_url_normalized = self.url.rstrip("/")
                canonical_url_normalized = canonical_url.rstrip("/")

                if current_url_normalized != canonical_url_normalized:
                    issues.append(
                        Issue(
                            url=self.url,
                            type="canonical_points_elsewhere",
                            severity="info",
                            detail=f"Canonical points to different URL: {canonical_url}",
                        )
                    )

                # Check for HTTP vs HTTPS mismatch
                current_scheme = self.parsed_url.scheme
                canonical_scheme = urlparse(canonical_url).scheme

                if current_scheme == "https" and canonical_scheme == "http":
                    issues.append(
                        Issue(
                            url=self.url,
                            type="canonical_http_on_https",
                            severity="high",
                            detail="HTTPS page has HTTP canonical - this can cause indexing issues",
                        )
                    )

        return issues

    def check_robots_meta(self) -> list[Issue]:
        """
        Check robots meta tag directives.

        Returns:
            List of robots meta tag issues
        """
        issues = []

        robots_tags = self.soup.find_all("meta", attrs={"name": lambda n: n and n.lower() == "robots"})

        if len(robots_tags) > 1:
            issues.append(
                Issue(
                    url=self.url,
                    type="multiple_robots_meta",
                    severity="medium",
                    detail=f"Multiple robots meta tags found ({len(robots_tags)})",
                )
            )

        for robots_tag in robots_tags:
            content = (robots_tag.get("content") or "").lower()

            if not content:
                continue

            directives = [d.strip() for d in content.split(",")]

            # Check for conflicting directives
            if "index" in directives and "noindex" in directives:
                issues.append(
                    Issue(
                        url=self.url,
                        type="conflicting_robots_directives",
                        severity="high",
                        detail="Conflicting robots directives: both 'index' and 'noindex'",
                    )
                )

            if "follow" in directives and "nofollow" in directives:
                issues.append(
                    Issue(
                        url=self.url,
                        type="conflicting_robots_directives",
                        severity="high",
                        detail="Conflicting robots directives: both 'follow' and 'nofollow'",
                    )
                )

            # Check for noindex
            if "noindex" in directives:
                issues.append(
                    Issue(
                        url=self.url,
                        type="noindex_directive",
                        severity="info",
                        detail="Page has noindex directive - will not be indexed by search engines",
                    )
                )

            # Check for nofollow
            if "nofollow" in directives:
                issues.append(
                    Issue(
                        url=self.url,
                        type="nofollow_directive",
                        severity="info",
                        detail="Page has nofollow directive - links will not be followed",
                    )
                )

            # Check for none (equivalent to noindex, nofollow)
            if "none" in directives:
                issues.append(
                    Issue(
                        url=self.url,
                        type="robots_none_directive",
                        severity="info",
                        detail="Page has 'none' directive (equivalent to noindex, nofollow)",
                    )
                )

            # Check for noarchive
            if "noarchive" in directives:
                issues.append(
                    Issue(
                        url=self.url,
                        type="noarchive_directive",
                        severity="info",
                        detail="Page has noarchive directive - cached copy will not be available",
                    )
                )

        return issues

    def check_meta_robots(self) -> list[Issue]:
        """
        Check for Googlebot-specific and other search engine specific robots meta tags.

        Returns:
            List of search engine specific robots issues
        """
        issues = []

        # Check for Googlebot-specific tags
        googlebot_tag = self.soup.find("meta", attrs={"name": lambda n: n and n.lower() == "googlebot"})
        general_robots = self.soup.find("meta", attrs={"name": lambda n: n and n.lower() == "robots"})

        if googlebot_tag and general_robots:
            google_content = (googlebot_tag.get("content") or "").lower()
            robots_content = (general_robots.get("content") or "").lower()

            if "noindex" in google_content and "noindex" not in robots_content:
                issues.append(
                    Issue(
                        url=self.url,
                        type="googlebot_noindex_mismatch",
                        severity="medium",
                        detail="Googlebot meta has noindex but general robots meta does not",
                    )
                )

        return issues

    def check_x_robots_tag(self) -> list[Issue]:
        """
        Note: X-Robots-Tag is an HTTP header, not in HTML.
        This method serves as a placeholder for header-based checks.

        Returns:
            Empty list (actual check would need HTTP headers)
        """
        # X-Robots-Tag is checked at the HTTP response level
        # This would be implemented in the crawler module
        return []


class SitemapValidator:
    """Validate XML sitemap structure and content."""

    def __init__(self, sitemap_xml: str, sitemap_url: str):
        """
        Initialize sitemap validator.

        Args:
            sitemap_xml: XML content of the sitemap
            sitemap_url: URL of the sitemap
        """
        self.xml = sitemap_xml
        self.url = sitemap_url
        self.soup = BeautifulSoup(sitemap_xml, "lxml-xml")

    def validate(self) -> list[Issue]:
        """
        Validate sitemap structure and content.

        Returns:
            List of sitemap issues
        """
        issues = []

        # Check if it's a valid sitemap
        if not self.soup.find("urlset") and not self.soup.find("sitemapindex"):
            issues.append(
                Issue(
                    url=self.url,
                    type="invalid_sitemap_format",
                    severity="high",
                    detail="Sitemap does not have valid urlset or sitemapindex root element",
                )
            )
            return issues

        # Check for URL count (max 50,000 per sitemap)
        urls = self.soup.find_all("url")
        if len(urls) > 50000:
            issues.append(
                Issue(
                    url=self.url,
                    type="sitemap_too_many_urls",
                    severity="high",
                    detail=f"Sitemap contains {len(urls)} URLs (max 50,000 recommended)",
                )
            )

        # Validate individual URLs
        for url_tag in urls[:100]:  # Sample first 100 to avoid performance issues
            loc = url_tag.find("loc")
            if not loc or not loc.string:
                issues.append(
                    Issue(
                        url=self.url,
                        type="sitemap_url_missing_loc",
                        severity="high",
                        detail="Sitemap URL entry missing <loc> element",
                    )
                )
                continue

            url_value = loc.string.strip()

            # Check if URL is absolute
            if not url_value.startswith(("http://", "https://")):
                issues.append(
                    Issue(
                        url=self.url,
                        type="sitemap_relative_url",
                        severity="high",
                        detail=f"Sitemap contains relative URL: {url_value}",
                    )
                )

            # Check for invalid characters
            if " " in url_value:
                issues.append(
                    Issue(
                        url=self.url,
                        type="sitemap_url_has_spaces",
                        severity="high",
                        detail=f"Sitemap URL contains spaces: {url_value}",
                    )
                )

            # Validate priority if present
            priority = url_tag.find("priority")
            if priority and priority.string:
                try:
                    priority_val = float(priority.string)
                    if priority_val < 0 or priority_val > 1:
                        issues.append(
                            Issue(
                                url=self.url,
                                type="sitemap_invalid_priority",
                                severity="medium",
                                detail=f"Priority must be between 0.0 and 1.0, got {priority_val}",
                            )
                        )
                except ValueError:
                    issues.append(
                        Issue(
                            url=self.url,
                            type="sitemap_invalid_priority",
                            severity="medium",
                            detail=f"Invalid priority value: {priority.string}",
                        )
                    )

            # Validate changefreq if present
            changefreq = url_tag.find("changefreq")
            if changefreq and changefreq.string:
                valid_values = [
                    "always",
                    "hourly",
                    "daily",
                    "weekly",
                    "monthly",
                    "yearly",
                    "never",
                ]
                if changefreq.string.lower() not in valid_values:
                    issues.append(
                        Issue(
                            url=self.url,
                            type="sitemap_invalid_changefreq",
                            severity="low",
                            detail=f"Invalid changefreq value: {changefreq.string}",
                        )
                    )

        return issues


def check_pagination(html: str, url: str) -> list[Issue]:
    """
    Check for proper pagination implementation.

    Args:
        html: HTML content to check
        url: URL of the page

    Returns:
        List of pagination issues
    """
    issues = []
    soup = BeautifulSoup(html, "lxml")

    # Check for rel="next" and rel="prev" links
    next_link = soup.find("link", rel="next")
    prev_link = soup.find("link", rel="prev")

    # If pagination is detected, validate implementation
    if next_link or prev_link:
        if next_link and not next_link.get("href"):
            issues.append(
                Issue(
                    url=url,
                    type="pagination_next_empty",
                    severity="medium",
                    detail="rel='next' link has no href attribute",
                )
            )

        if prev_link and not prev_link.get("href"):
            issues.append(
                Issue(
                    url=url,
                    type="pagination_prev_empty",
                    severity="medium",
                    detail="rel='prev' link has no href attribute",
                )
            )

    return issues
