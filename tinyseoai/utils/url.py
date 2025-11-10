from __future__ import annotations
from urllib.parse import urlparse, urlunparse

def normalize_url(u: str) -> str:
    p = urlparse(u.strip())
    scheme = p.scheme or "https"
    netloc = p.netloc.lower()
    path = p.path or "/"
    # Remove fragments & normalize
    return urlunparse((scheme, netloc, path, "", "", ""))

def same_host(url: str, host: str) -> bool:
    return urlparse(url).netloc.lower() == host.lower()
