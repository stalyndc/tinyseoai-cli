"""
Performance checks for page speed optimization and Core Web Vitals indicators.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ...data.models import Issue


class PerformanceChecker:
    """Check performance-related SEO factors."""

    def __init__(self, html: str, url: str, response_headers: dict | None = None):
        """
        Initialize performance checker.

        Args:
            html: HTML content to check
            url: URL of the page
            response_headers: HTTP response headers
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, "lxml")
        self.headers = response_headers or {}

    def check_all(self) -> list[Issue]:
        """
        Run all performance checks.

        Returns:
            List of performance issues
        """
        issues = []

        issues.extend(self.check_images())
        issues.extend(self.check_render_blocking_resources())
        issues.extend(self.check_compression())
        issues.extend(self.check_caching())
        issues.extend(self.check_page_size())
        issues.extend(self.check_preconnect())

        return issues

    def check_images(self) -> list[Issue]:
        """
        Check image optimization.

        Returns:
            List of image-related performance issues
        """
        issues = []

        images = self.soup.find_all("img")

        # Check for images without width/height (causes layout shift)
        images_without_dimensions = 0
        images_without_lazy_loading = 0
        images_without_modern_format = 0

        for img in images:
            src = img.get("src", "")

            # Check for dimensions
            if not img.get("width") or not img.get("height"):
                images_without_dimensions += 1

            # Check for lazy loading
            loading = img.get("loading", "").lower()
            if loading != "lazy" and not img.get("data-src"):  # data-src indicates JS lazy loading
                images_without_lazy_loading += 1

            # Check for modern image formats
            if src and not any(ext in src.lower() for ext in [".webp", ".avif"]):
                images_without_modern_format += 1

        if images_without_dimensions > 0:
            issues.append(
                Issue(
                    url=self.url,
                    type="images_without_dimensions",
                    severity="medium",
                    detail=f"{images_without_dimensions} image(s) missing width/height attributes. "
                    "This can cause Cumulative Layout Shift (CLS).",
                )
            )

        if images_without_lazy_loading > 3:  # Allow a few above-fold images
            issues.append(
                Issue(
                    url=self.url,
                    type="images_not_lazy_loaded",
                    severity="low",
                    detail=f"{images_without_lazy_loading} image(s) not lazy loaded. "
                    "Consider using loading='lazy' for off-screen images.",
                )
            )

        if images_without_modern_format > 0:
            issues.append(
                Issue(
                    url=self.url,
                    type="images_not_modern_format",
                    severity="info",
                    detail=f"{images_without_modern_format} image(s) not using modern formats (WebP/AVIF). "
                    "Modern formats can significantly reduce file size.",
                )
            )

        return issues

    def check_render_blocking_resources(self) -> list[Issue]:
        """
        Check for render-blocking CSS and JavaScript.

        Returns:
            List of render-blocking resource issues
        """
        issues = []

        # Check CSS
        css_links = self.soup.find_all("link", rel="stylesheet")
        blocking_css = 0

        for link in css_links:
            media = link.get("media", "all")
            # CSS is render-blocking unless it has media query
            if media == "all" or not media:
                blocking_css += 1

        if blocking_css > 2:
            issues.append(
                Issue(
                    url=self.url,
                    type="render_blocking_css",
                    severity="medium",
                    detail=f"{blocking_css} render-blocking CSS file(s). "
                    "Consider inlining critical CSS or using media queries.",
                )
            )

        # Check JavaScript
        scripts = self.soup.find_all("script", src=True)
        blocking_scripts = 0

        for script in scripts:
            # Scripts are render-blocking unless they have async or defer
            if not script.get("async") and not script.get("defer"):
                # Check if it's in <head>
                if script.find_parent("head"):
                    blocking_scripts += 1

        if blocking_scripts > 0:
            issues.append(
                Issue(
                    url=self.url,
                    type="render_blocking_javascript",
                    severity="high",
                    detail=f"{blocking_scripts} render-blocking JavaScript file(s) in <head>. "
                    "Add async or defer attributes, or move scripts to end of <body>.",
                )
            )

        return issues

    def check_compression(self) -> list[Issue]:
        """
        Check if compression is enabled.

        Returns:
            List of compression issues
        """
        issues = []

        headers_lower = {k.lower(): v for k, v in self.headers.items()}

        # Check for compression
        content_encoding = headers_lower.get("content-encoding", "").lower()

        if not content_encoding or content_encoding not in ["gzip", "br", "deflate"]:
            issues.append(
                Issue(
                    url=self.url,
                    type="no_compression",
                    severity="high",
                    detail="No compression detected. Enable gzip or Brotli compression to reduce transfer size.",
                )
            )
        elif content_encoding == "gzip":
            # Brotli is better than gzip
            issues.append(
                Issue(
                    url=self.url,
                    type="compression_not_optimal",
                    severity="info",
                    detail="Using gzip compression. Consider Brotli for better compression ratios.",
                )
            )

        return issues

    def check_caching(self) -> list[Issue]:
        """
        Check caching headers.

        Returns:
            List of caching issues
        """
        issues = []

        headers_lower = {k.lower(): v for k, v in self.headers.items()}

        cache_control = headers_lower.get("cache-control", "").lower()
        expires = headers_lower.get("expires")
        etag = headers_lower.get("etag")

        # Check for caching headers
        if not cache_control and not expires:
            issues.append(
                Issue(
                    url=self.url,
                    type="no_caching_headers",
                    severity="medium",
                    detail="No caching headers found. Set Cache-Control or Expires for better performance.",
                )
            )
        elif cache_control:
            # Check if cache is disabled
            if "no-cache" in cache_control or "no-store" in cache_control:
                issues.append(
                    Issue(
                        url=self.url,
                        type="caching_disabled",
                        severity="medium",
                        detail="Caching is disabled via Cache-Control header. "
                        "Consider enabling caching for static resources.",
                    )
                )

            # Check for short cache duration
            max_age_match = re.search(r"max-age=(\d+)", cache_control)
            if max_age_match:
                max_age = int(max_age_match.group(1))
                if max_age < 3600:  # Less than 1 hour
                    issues.append(
                        Issue(
                            url=self.url,
                            type="short_cache_duration",
                            severity="low",
                            detail=f"Cache duration is only {max_age} seconds. "
                            "Consider longer cache for static resources.",
                        )
                    )

        # Check for ETag
        if not etag:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_etag",
                    severity="info",
                    detail="Missing ETag header. ETags help with cache validation.",
                )
            )

        return issues

    def check_page_size(self) -> list[Issue]:
        """
        Check estimated page size.

        Returns:
            List of page size issues
        """
        issues = []

        html_size = len(self.html.encode("utf-8"))
        html_size_kb = html_size / 1024

        if html_size_kb > 500:  # 500 KB
            issues.append(
                Issue(
                    url=self.url,
                    type="large_html_size",
                    severity="high",
                    detail=f"HTML size is {html_size_kb:.1f} KB. Large HTML can slow initial render. "
                    "Consider code minification and removing unused code.",
                )
            )
        elif html_size_kb > 200:  # 200 KB
            issues.append(
                Issue(
                    url=self.url,
                    type="moderate_html_size",
                    severity="low",
                    detail=f"HTML size is {html_size_kb:.1f} KB. Consider optimizing if possible.",
                )
            )

        # Count external resources
        external_css = len(self.soup.find_all("link", rel="stylesheet"))
        external_js = len(self.soup.find_all("script", src=True))

        if external_css > 5:
            issues.append(
                Issue(
                    url=self.url,
                    type="too_many_css_files",
                    severity="medium",
                    detail=f"{external_css} external CSS files. Consider concatenation to reduce HTTP requests.",
                )
            )

        if external_js > 10:
            issues.append(
                Issue(
                    url=self.url,
                    type="too_many_js_files",
                    severity="medium",
                    detail=f"{external_js} external JavaScript files. "
                    "Consider bundling to reduce HTTP requests.",
                )
            )

        return issues

    def check_preconnect(self) -> list[Issue]:
        """
        Check for resource hints (preconnect, dns-prefetch, preload).

        Returns:
            List of resource hint issues
        """
        issues = []

        # Get all external domains from resources
        external_domains = set()

        for tag in self.soup.find_all(["link", "script", "img"], src=True):
            src = tag.get("src") or tag.get("href", "")
            if src.startswith("http"):
                domain = urlparse(src).netloc
                if domain and domain != urlparse(self.url).netloc:
                    external_domains.add(domain)

        # Check for preconnect hints
        preconnects = self.soup.find_all("link", rel="preconnect")
        preconnect_domains = {urlparse(link.get("href", "")).netloc for link in preconnects}

        # Find domains that could benefit from preconnect
        missing_preconnect = external_domains - preconnect_domains

        if len(missing_preconnect) > 0:
            sample_domains = list(missing_preconnect)[:3]
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_preconnect",
                    severity="info",
                    detail=f"Consider adding preconnect hints for external domains: "
                    f"{', '.join(sample_domains)}. This can improve loading performance.",
                )
            )

        return issues

    def get_performance_metrics(self) -> dict[str, any]:
        """
        Get performance-related metrics.

        Returns:
            Dictionary with performance metrics
        """
        return {
            "html_size_kb": len(self.html.encode("utf-8")) / 1024,
            "total_images": len(self.soup.find_all("img")),
            "external_css": len(self.soup.find_all("link", rel="stylesheet")),
            "external_js": len(self.soup.find_all("script", src=True)),
            "inline_scripts": len(self.soup.find_all("script", src=False)),
            "has_compression": "content-encoding" in {k.lower() for k in self.headers.keys()},
            "has_caching": "cache-control" in {k.lower() for k in self.headers.keys()},
        }
