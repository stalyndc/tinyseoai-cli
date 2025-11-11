"""
Security checks for HTTPS, headers, and SSL validation.
"""
from __future__ import annotations

from urllib.parse import urlparse

import httpx
from loguru import logger

from ...data.models import Issue


class SecurityChecker:
    """Perform security-related SEO checks."""

    def __init__(self, url: str):
        """
        Initialize the security checker.

        Args:
            url: URL to check
        """
        self.url = url
        self.parsed = urlparse(url)
        self.is_https = self.parsed.scheme == "https"

    async def check_all(self, client: httpx.AsyncClient) -> list[Issue]:
        """
        Run all security checks.

        Args:
            client: HTTP client to use

        Returns:
            List of security issues found
        """
        issues = []

        # Check HTTPS
        issues.extend(self.check_https())

        # Check security headers
        try:
            response = await client.get(self.url, timeout=15.0)
            issues.extend(self.check_security_headers(response.headers))
            issues.extend(self.check_mixed_content(response.text))
        except Exception as e:
            logger.error(f"Error checking security for {self.url}: {e}")

        return issues

    def check_https(self) -> list[Issue]:
        """
        Check if the site uses HTTPS.

        Returns:
            List of HTTPS-related issues
        """
        issues = []

        if not self.is_https:
            issues.append(
                Issue(
                    url=self.url,
                    type="no_https",
                    severity="high",
                    detail="Site is not using HTTPS. This can negatively impact SEO and user trust.",
                )
            )

        return issues

    def check_security_headers(self, headers: dict) -> list[Issue]:
        """
        Check for important security headers.

        Args:
            headers: HTTP response headers

        Returns:
            List of security header issues
        """
        issues = []

        # Convert header keys to lowercase for case-insensitive comparison
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Check for HSTS (HTTP Strict Transport Security)
        if self.is_https and "strict-transport-security" not in headers_lower:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_hsts",
                    severity="medium",
                    detail="Missing Strict-Transport-Security header. "
                    "This header enforces HTTPS connections.",
                )
            )

        # Check for X-Content-Type-Options
        if "x-content-type-options" not in headers_lower:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_x_content_type_options",
                    severity="low",
                    detail="Missing X-Content-Type-Options header. "
                    "Should be set to 'nosniff' to prevent MIME type sniffing.",
                )
            )

        # Check for X-Frame-Options or CSP frame-ancestors
        if (
            "x-frame-options" not in headers_lower
            and "content-security-policy" not in headers_lower
        ):
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_clickjacking_protection",
                    severity="medium",
                    detail="Missing X-Frame-Options or CSP frame-ancestors directive. "
                    "This protects against clickjacking attacks.",
                )
            )

        # Check for Content-Security-Policy
        if "content-security-policy" not in headers_lower:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_csp",
                    severity="low",
                    detail="Missing Content-Security-Policy header. "
                    "CSP helps prevent XSS and other code injection attacks.",
                )
            )

        # Check for X-XSS-Protection
        if "x-xss-protection" not in headers_lower:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_xss_protection",
                    severity="low",
                    detail="Missing X-XSS-Protection header. "
                    "This header enables browser XSS filtering.",
                )
            )

        # Check for Referrer-Policy
        if "referrer-policy" not in headers_lower:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_referrer_policy",
                    severity="info",
                    detail="Missing Referrer-Policy header. "
                    "This controls how much referrer information is shared.",
                )
            )

        # Check for Permissions-Policy (formerly Feature-Policy)
        if (
            "permissions-policy" not in headers_lower
            and "feature-policy" not in headers_lower
        ):
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_permissions_policy",
                    severity="info",
                    detail="Missing Permissions-Policy header. "
                    "This controls which browser features can be used.",
                )
            )

        return issues

    def check_mixed_content(self, html: str) -> list[Issue]:
        """
        Check for mixed content (HTTP resources on HTTPS pages).

        Args:
            html: HTML content to check

        Returns:
            List of mixed content issues
        """
        issues = []

        if not self.is_https:
            return issues  # Only relevant for HTTPS sites

        # Check for HTTP resources in HTML
        import re

        # Pattern to find HTTP URLs in common attributes
        http_pattern = re.compile(
            r'(?:src|href|data|action)=["\']http://[^"\']+["\']', re.IGNORECASE
        )

        matches = http_pattern.findall(html)

        if matches:
            # Sample a few for the detail
            sample = matches[:5]
            issues.append(
                Issue(
                    url=self.url,
                    type="mixed_content",
                    severity="high",
                    detail=f"Found {len(matches)} HTTP resources on HTTPS page. "
                    f"Examples: {', '.join(sample[:3])}",
                )
            )

        return issues


async def check_ssl_certificate(url: str) -> list[Issue]:
    """
    Check SSL certificate validity.

    Args:
        url: URL to check

    Returns:
        List of SSL certificate issues
    """
    issues = []
    parsed = urlparse(url)

    if parsed.scheme != "https":
        return issues  # Only check HTTPS sites

    try:
        import socket
        import ssl
        from datetime import datetime

        context = ssl.create_default_context()
        with socket.create_connection((parsed.netloc, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=parsed.netloc) as ssock:
                cert = ssock.getpeercert()

                # Check expiration
                not_after = datetime.strptime(
                    cert["notAfter"], "%b %d %H:%M:%S %Y %GMT"
                )
                days_until_expiry = (not_after - datetime.now()).days

                if days_until_expiry < 0:
                    issues.append(
                        Issue(
                            url=url,
                            type="ssl_expired",
                            severity="high",
                            detail=f"SSL certificate expired {abs(days_until_expiry)} days ago",
                        )
                    )
                elif days_until_expiry < 30:
                    issues.append(
                        Issue(
                            url=url,
                            type="ssl_expiring_soon",
                            severity="medium",
                            detail=f"SSL certificate expires in {days_until_expiry} days",
                        )
                    )

                # Check for self-signed certificate
                issuer = dict(x[0] for x in cert.get("issuer", []))
                subject = dict(x[0] for x in cert.get("subject", []))

                if issuer == subject:
                    issues.append(
                        Issue(
                            url=url,
                            type="self_signed_certificate",
                            severity="high",
                            detail="SSL certificate is self-signed",
                        )
                    )

    except ssl.SSLError as e:
        issues.append(
            Issue(url=url, type="ssl_error", severity="high", detail=f"SSL error: {str(e)}")
        )
    except Exception as e:
        logger.warning(f"Could not check SSL certificate for {url}: {e}")

    return issues


def check_cookies(headers: dict) -> list[Issue]:
    """
    Check cookie security settings.

    Args:
        headers: HTTP response headers

    Returns:
        List of cookie security issues
    """
    issues = []
    headers_lower = {k.lower(): v for k, v in headers.items()}

    set_cookie = headers_lower.get("set-cookie", "")

    if set_cookie:
        # Check for Secure flag
        if "secure" not in set_cookie.lower():
            issues.append(
                Issue(
                    url="",
                    type="cookie_missing_secure",
                    severity="medium",
                    detail="Cookies are missing the Secure flag",
                )
            )

        # Check for HttpOnly flag
        if "httponly" not in set_cookie.lower():
            issues.append(
                Issue(
                    url="",
                    type="cookie_missing_httponly",
                    severity="medium",
                    detail="Cookies are missing the HttpOnly flag",
                )
            )

        # Check for SameSite attribute
        if "samesite" not in set_cookie.lower():
            issues.append(
                Issue(
                    url="",
                    type="cookie_missing_samesite",
                    severity="low",
                    detail="Cookies are missing the SameSite attribute",
                )
            )

    return issues
