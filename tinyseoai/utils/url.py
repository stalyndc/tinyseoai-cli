from __future__ import annotations
from urllib.parse import urlparse, urlunparse
import ipaddress


class URLValidationError(ValueError):
    """Raised when URL validation fails."""
    pass


def validate_url(url: str) -> str:
    """
    Validate URL for security and correctness.

    BUGFIX: Added URL validation to prevent SSRF attacks and invalid input.
    See: BUGFIXES.md #2

    Args:
        url: URL string to validate

    Returns:
        Validated URL string

    Raises:
        URLValidationError: If URL is invalid or potentially dangerous
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL must be a non-empty string")

    url = url.strip()
    if not url:
        raise URLValidationError("URL cannot be empty or whitespace")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise URLValidationError(f"Invalid URL format: {e}")

    # Check scheme
    if parsed.scheme not in ("http", "https"):
        raise URLValidationError(
            f"Only HTTP/HTTPS protocols are allowed, got: {parsed.scheme or 'none'}"
        )

    # Check netloc exists
    if not parsed.netloc:
        raise URLValidationError("URL must have a valid domain")

    # Prevent SSRF: block private/local addresses
    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("URL must have a valid hostname")

    # Block localhost and private networks
    blocked_hosts = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "[::1]",
    }

    if hostname.lower() in blocked_hosts:
        raise URLValidationError(f"Cannot audit local/private addresses: {hostname}")

    # Check for private IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            raise URLValidationError(f"Cannot audit private IP address: {hostname}")
    except ValueError:
        # Not an IP address, that's fine (it's a domain name)
        pass

    # Block common internal TLDs
    if hostname.endswith((".local", ".internal", ".localhost")):
        raise URLValidationError(f"Cannot audit internal domain: {hostname}")

    return url


def normalize_url(u: str) -> str:
    """
    Normalize URL to canonical form.

    BUGFIX: Added error handling for invalid input.
    See: BUGFIXES.md #3

    Args:
        u: URL string to normalize

    Returns:
        Normalized URL string

    Raises:
        URLValidationError: If URL cannot be parsed
    """
    if not u or not isinstance(u, str):
        raise URLValidationError("URL must be a non-empty string")

    u = u.strip()
    if not u:
        raise URLValidationError("URL cannot be empty")

    try:
        p = urlparse(u)
    except Exception as e:
        raise URLValidationError(f"Failed to parse URL: {e}")

    scheme = p.scheme or "https"
    netloc = p.netloc.lower() if p.netloc else ""

    if not netloc:
        raise URLValidationError(f"Invalid URL: missing domain in '{u}'")

    path = p.path or "/"

    # Remove fragments & normalize
    return urlunparse((scheme, netloc, path, "", "", ""))


def same_host(url: str, host: str) -> bool:
    """Check if URL belongs to the same host."""
    try:
        return urlparse(url).netloc.lower() == host.lower()
    except Exception:
        return False
