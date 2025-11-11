"""
Comprehensive link analysis including link graphs, orphan pages, and redirect chains.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

import httpx
from loguru import logger

from ...data.models import Issue


class LinkGraph:
    """Build and analyze link graph for a website."""

    def __init__(self):
        """Initialize the link graph."""
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # source -> targets
        self.backlinks: Dict[str, Set[str]] = defaultdict(set)  # target -> sources
        self.anchor_texts: Dict[Tuple[str, str], List[str]] = defaultdict(list)

    def add_page(self, url: str) -> None:
        """
        Add a page to the graph.

        Args:
            url: URL of the page
        """
        self.nodes.add(url)

    def add_link(self, source: str, target: str, anchor_text: str = "") -> None:
        """
        Add a link between two pages.

        Args:
            source: Source URL
            target: Target URL
            anchor_text: Anchor text of the link
        """
        self.nodes.add(source)
        self.nodes.add(target)
        self.edges[source].add(target)
        self.backlinks[target].add(source)

        if anchor_text:
            self.anchor_texts[(source, target)].append(anchor_text)

    def get_orphan_pages(self) -> List[str]:
        """
        Find pages with no internal links pointing to them (orphans).

        Returns:
            List of orphan page URLs
        """
        orphans = []

        for node in self.nodes:
            # A page is orphaned if it has no backlinks
            # (except if it's the homepage/entry point)
            if len(self.backlinks[node]) == 0:
                orphans.append(node)

        return orphans

    def get_page_depth(self, start_url: str) -> Dict[str, int]:
        """
        Calculate the depth of each page from the start URL using BFS.

        Args:
            start_url: Starting URL (usually homepage)

        Returns:
            Dictionary mapping URLs to their depth from start
        """
        from collections import deque

        depths = {start_url: 0}
        queue = deque([start_url])

        while queue:
            current = queue.popleft()
            current_depth = depths[current]

            for target in self.edges.get(current, set()):
                if target not in depths:
                    depths[target] = current_depth + 1
                    queue.append(target)

        return depths

    def get_pages_beyond_depth(self, start_url: str, max_depth: int = 3) -> List[str]:
        """
        Find pages that are too many clicks away from the homepage.

        Args:
            start_url: Starting URL (usually homepage)
            max_depth: Maximum acceptable depth

        Returns:
            List of URLs beyond max depth
        """
        depths = self.get_page_depth(start_url)
        return [url for url, depth in depths.items() if depth > max_depth]

    def get_page_metrics(self, url: str) -> Dict[str, int]:
        """
        Get metrics for a specific page.

        Args:
            url: URL to analyze

        Returns:
            Dictionary with page metrics
        """
        return {
            "outbound_links": len(self.edges.get(url, set())),
            "inbound_links": len(self.backlinks.get(url, set())),
            "unique_anchor_texts": len(
                set(
                    anchor
                    for (src, tgt), anchors in self.anchor_texts.items()
                    if tgt == url
                    for anchor in anchors
                )
            ),
        }

    def get_hub_pages(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Find hub pages (pages with many outbound links).

        Args:
            top_n: Number of top hubs to return

        Returns:
            List of (URL, outbound_count) tuples
        """
        hubs = [(url, len(targets)) for url, targets in self.edges.items()]
        hubs.sort(key=lambda x: x[1], reverse=True)
        return hubs[:top_n]

    def get_authority_pages(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Find authority pages (pages with many inbound links).

        Args:
            top_n: Number of top authorities to return

        Returns:
            List of (URL, inbound_count) tuples
        """
        authorities = [(url, len(sources)) for url, sources in self.backlinks.items()]
        authorities.sort(key=lambda x: x[1], reverse=True)
        return authorities[:top_n]


class LinkChecker:
    """Check links for various issues."""

    def __init__(self, base_url: str):
        """
        Initialize link checker.

        Args:
            base_url: Base URL of the website
        """
        self.base_url = base_url
        self.link_graph = LinkGraph()

    def analyze_internal_linking(
        self, pages_data: List[Dict[str, any]]
    ) -> List[Issue]:
        """
        Analyze internal linking structure.

        Args:
            pages_data: List of page data dictionaries with URLs and links

        Returns:
            List of internal linking issues
        """
        issues = []

        # Build link graph
        for page in pages_data:
            url = page.get("url")
            internal_links = page.get("internal_links", [])

            self.link_graph.add_page(url)

            for link_data in internal_links:
                target = link_data.get("url")
                anchor = link_data.get("anchor_text", "")
                self.link_graph.add_link(url, target, anchor)

        # Find orphan pages
        orphans = self.link_graph.get_orphan_pages()
        if len(orphans) > 1:  # More than just the homepage
            for orphan in orphans[:10]:  # Sample first 10
                issues.append(
                    Issue(
                        url=orphan,
                        type="orphan_page",
                        severity="medium",
                        detail="Page has no internal links pointing to it (orphan page)",
                    )
                )

        # Find pages too deep in site structure
        if pages_data:
            start_url = pages_data[0].get("url")  # Assume first is homepage
            deep_pages = self.link_graph.get_pages_beyond_depth(start_url, max_depth=3)

            for deep_page in deep_pages[:10]:  # Sample first 10
                issues.append(
                    Issue(
                        url=deep_page,
                        type="page_too_deep",
                        severity="low",
                        detail="Page is more than 3 clicks from homepage",
                    )
                )

        return issues

    def check_anchor_text(self, links: List[Dict[str, str]], url: str) -> List[Issue]:
        """
        Check anchor text quality.

        Args:
            links: List of link dictionaries
            url: URL of the page containing the links

        Returns:
            List of anchor text issues
        """
        issues = []

        for link in links:
            anchor = link.get("anchor_text", "").strip()
            target = link.get("url", "")

            # Check for empty anchor text
            if not anchor:
                issues.append(
                    Issue(
                        url=url,
                        type="empty_anchor_text",
                        severity="low",
                        detail=f"Link to {target} has no anchor text",
                    )
                )

            # Check for generic anchor text
            generic_anchors = [
                "click here",
                "read more",
                "learn more",
                "here",
                "this",
                "link",
                "more",
            ]
            if anchor.lower() in generic_anchors:
                issues.append(
                    Issue(
                        url=url,
                        type="generic_anchor_text",
                        severity="low",
                        detail=f"Generic anchor text '{anchor}' on link to {target}",
                    )
                )

            # Check for over-optimized anchor text (all caps)
            if anchor.isupper() and len(anchor) > 3:
                issues.append(
                    Issue(
                        url=url,
                        type="anchor_text_all_caps",
                        severity="info",
                        detail=f"Anchor text is all caps: '{anchor}'",
                    )
                )

        return issues

    def check_link_attributes(
        self, links: List[Dict[str, any]], url: str
    ) -> List[Issue]:
        """
        Check link attributes like rel, target, etc.

        Args:
            links: List of link dictionaries
            url: URL of the page

        Returns:
            List of link attribute issues
        """
        issues = []

        for link in links:
            rel = link.get("rel", [])
            target = link.get("target")
            href = link.get("url", "")

            # Check external links for nofollow
            if not href.startswith(self.base_url):
                if "nofollow" not in rel:
                    # This is informational - not always an issue
                    pass  # External links don't always need nofollow

                # Check for target="_blank" without rel="noopener"
                if target == "_blank" and "noopener" not in rel:
                    issues.append(
                        Issue(
                            url=url,
                            type="external_link_missing_noopener",
                            severity="medium",
                            detail=f"External link with target='_blank' should have rel='noopener': {href}",
                        )
                    )

        return issues


async def check_redirect_chains(
    url: str, client: httpx.AsyncClient, max_redirects: int = 10
) -> List[Issue]:
    """
    Check for redirect chains and loops.

    Args:
        url: URL to check
        client: HTTP client
        max_redirects: Maximum number of redirects to follow

    Returns:
        List of redirect issues
    """
    issues = []
    visited = []

    try:
        # Manually follow redirects to track the chain
        current_url = url
        redirect_count = 0

        while redirect_count < max_redirects:
            response = await client.get(
                current_url, follow_redirects=False, timeout=10.0
            )
            visited.append((current_url, response.status_code))

            if response.status_code in (301, 302, 303, 307, 308):
                redirect_count += 1
                location = response.headers.get("location")

                if not location:
                    issues.append(
                        Issue(
                            url=url,
                            type="redirect_missing_location",
                            severity="high",
                            detail=f"Redirect ({response.status_code}) without Location header",
                        )
                    )
                    break

                # Make location absolute
                from urllib.parse import urljoin

                next_url = urljoin(current_url, location)

                # Check for redirect loop
                if next_url in [v[0] for v in visited]:
                    issues.append(
                        Issue(
                            url=url,
                            type="redirect_loop",
                            severity="high",
                            detail=f"Redirect loop detected: {' -> '.join([v[0] for v in visited])}",
                        )
                    )
                    break

                current_url = next_url
            else:
                # Not a redirect, we're done
                break

        # Check if we have a redirect chain (more than 1 redirect)
        if redirect_count > 1:
            issues.append(
                Issue(
                    url=url,
                    type="redirect_chain",
                    severity="medium",
                    detail=f"Redirect chain of {redirect_count} hops detected",
                )
            )

        # Check for temporary redirects that should be permanent
        if redirect_count > 0:
            first_redirect_status = visited[0][1]
            if first_redirect_status in (302, 307):
                issues.append(
                    Issue(
                        url=url,
                        type="temporary_redirect",
                        severity="info",
                        detail=f"Using temporary redirect ({first_redirect_status}). "
                        "Consider 301 for permanent moves.",
                    )
                )

    except Exception as e:
        logger.warning(f"Error checking redirects for {url}: {e}")

    return issues


def analyze_link_distribution(pages_data: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Analyze the distribution of internal links across pages.

    Args:
        pages_data: List of page data dictionaries

    Returns:
        Dictionary with link distribution statistics
    """
    if not pages_data:
        return {}

    outbound_counts = [len(page.get("internal_links", [])) for page in pages_data]

    return {
        "total_pages": len(pages_data),
        "avg_internal_links": sum(outbound_counts) / len(outbound_counts)
        if outbound_counts
        else 0,
        "max_internal_links": max(outbound_counts) if outbound_counts else 0,
        "min_internal_links": min(outbound_counts) if outbound_counts else 0,
        "pages_with_no_internal_links": sum(1 for count in outbound_counts if count == 0),
    }
