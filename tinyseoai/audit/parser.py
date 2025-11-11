"""
Enhanced HTML parsing and structured data extraction.
"""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from loguru import logger


class StructuredDataParser:
    """Extract and validate structured data (JSON-LD, Microdata, RDFa)."""

    def __init__(self, html: str, url: str):
        """
        Initialize the parser.

        Args:
            html: HTML content to parse
            url: URL of the page (for context)
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, "lxml")
        self.json_ld: list[dict[str, Any]] = []
        self.microdata: list[dict[str, Any]] = []
        self.rdfa: list[dict[str, Any]] = []

    def extract_all(self) -> dict[str, Any]:
        """
        Extract all types of structured data.

        Returns:
            Dictionary containing all extracted structured data
        """
        self._extract_json_ld()
        self._extract_microdata()
        self._extract_rdfa()

        return {
            "json_ld": self.json_ld,
            "microdata": self.microdata,
            "rdfa": self.rdfa,
            "total_schemas": len(self.json_ld) + len(self.microdata) + len(self.rdfa),
        }

    def _extract_json_ld(self) -> None:
        """Extract JSON-LD structured data."""
        scripts = self.soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                if script.string:
                    data = json.loads(script.string)
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        self.json_ld.extend(data)
                    else:
                        self.json_ld.append(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON-LD on {self.url}: {e}")

    def _extract_microdata(self) -> None:
        """Extract Microdata structured data."""
        items = self.soup.find_all(attrs={"itemscope": True})

        for item in items:
            try:
                schema_data = self._parse_microdata_item(item)
                if schema_data:
                    self.microdata.append(schema_data)
            except Exception as e:
                logger.warning(f"Error parsing microdata on {self.url}: {e}")

    def _parse_microdata_item(self, item: Tag) -> dict[str, Any] | None:
        """Parse a single microdata item."""
        item_type = item.get("itemtype")
        if not item_type:
            return None

        data = {"@type": item_type}

        # Extract properties
        properties = item.find_all(attrs={"itemprop": True})
        for prop in properties:
            prop_name = prop.get("itemprop")
            prop_value = self._get_microdata_value(prop)
            if prop_name and prop_value:
                data[prop_name] = prop_value

        return data

    def _get_microdata_value(self, element: Tag) -> Any:
        """Extract value from a microdata property."""
        # Check for nested itemscope
        if element.get("itemscope"):
            return self._parse_microdata_item(element)

        # Get value based on element type
        if element.name in ["meta", "link"]:
            return element.get("content") or element.get("href")
        elif element.name == "img":
            return element.get("src")
        elif element.name == "time":
            return element.get("datetime") or element.get_text().strip()
        else:
            return element.get_text().strip()

    def _extract_rdfa(self) -> None:
        """Extract RDFa structured data."""
        # Look for elements with RDFa properties
        elements = self.soup.find_all(attrs={"property": True})

        for element in elements:
            try:
                prop = element.get("property")
                content = element.get("content") or element.get_text().strip()
                if prop and content:
                    self.rdfa.append({"property": prop, "content": content})
            except Exception as e:
                logger.warning(f"Error parsing RDFa on {self.url}: {e}")

    def get_schema_types(self) -> list[str]:
        """
        Get all schema.org types found on the page.

        Returns:
            List of schema types
        """
        types = []

        # From JSON-LD
        for item in self.json_ld:
            if "@type" in item:
                types.append(item["@type"])

        # From Microdata
        for item in self.microdata:
            if "@type" in item:
                types.append(item["@type"])

        return types

    def has_schema_type(self, schema_type: str) -> bool:
        """
        Check if page has a specific schema type.

        Args:
            schema_type: Schema type to check for (e.g., "Article", "Product")

        Returns:
            True if schema type is present
        """
        return schema_type in self.get_schema_types()


class ContentParser:
    """Enhanced content extraction and analysis."""

    def __init__(self, html: str, url: str):
        """
        Initialize the content parser.

        Args:
            html: HTML content to parse
            url: URL of the page
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, "lxml")

    def extract_headings(self) -> dict[str, list[str]]:
        """
        Extract all headings with hierarchy.

        Returns:
            Dictionary mapping heading levels (h1-h6) to lists of heading text
        """
        headings = {}

        for level in range(1, 7):
            tag_name = f"h{level}"
            tags = self.soup.find_all(tag_name)
            headings[tag_name] = [tag.get_text().strip() for tag in tags]

        return headings

    def validate_heading_hierarchy(self) -> list[str]:
        """
        Validate heading hierarchy for SEO best practices.

        Returns:
            List of issues found
        """
        issues = []
        headings = self.extract_headings()

        # Check for single H1
        h1_count = len(headings.get("h1", []))
        if h1_count == 0:
            issues.append("No H1 heading found")
        elif h1_count > 1:
            issues.append(f"Multiple H1 headings found ({h1_count})")

        # Check for heading hierarchy skips
        levels_present = [
            level for level in range(1, 7) if headings.get(f"h{level}")
        ]

        if levels_present:
            for i in range(len(levels_present) - 1):
                if levels_present[i + 1] - levels_present[i] > 1:
                    issues.append(
                        f"Heading hierarchy skip: h{levels_present[i]} to "
                        f"h{levels_present[i + 1]}"
                    )

        return issues

    def extract_images(self) -> list[dict[str, str | None]]:
        """
        Extract all images with metadata.

        Returns:
            List of image data dictionaries
        """
        images = []
        img_tags = self.soup.find_all("img")

        for img in img_tags:
            images.append({
                "src": img.get("src"),
                "alt": img.get("alt"),
                "title": img.get("title"),
                "width": img.get("width"),
                "height": img.get("height"),
                "loading": img.get("loading"),
            })

        return images

    def check_images_have_alt(self) -> dict[str, Any]:
        """
        Check if all images have alt text.

        Returns:
            Dictionary with alt text statistics
        """
        images = self.extract_images()
        total = len(images)
        with_alt = sum(1 for img in images if img.get("alt"))
        missing_alt = total - with_alt

        return {
            "total_images": total,
            "with_alt": with_alt,
            "missing_alt": missing_alt,
            "missing_alt_percentage": (missing_alt / total * 100) if total > 0 else 0,
        }

    def extract_main_content(self) -> str | None:
        """
        Extract main content text from the page.

        Returns:
            Main content text or None
        """
        # Try to find main content area
        main = (
            self.soup.find("main")
            or self.soup.find("article")
            or self.soup.find(id=re.compile("content|main", re.I))
            or self.soup.find(class_=re.compile("content|main", re.I))
        )

        if main:
            # Remove script and style elements
            for element in main.find_all(["script", "style"]):
                element.decompose()

            return main.get_text(separator=" ", strip=True)

        # Fallback to body content
        body = self.soup.find("body")
        if body:
            for element in body.find_all(["script", "style", "nav", "header", "footer"]):
                element.decompose()
            return body.get_text(separator=" ", strip=True)

        return None

    def extract_word_count(self) -> int:
        """
        Extract word count from main content.

        Returns:
            Number of words in main content
        """
        content = self.extract_main_content()
        if not content:
            return 0

        words = content.split()
        return len(words)

    def extract_internal_links(self, base_url: str) -> list[dict[str, str]]:
        """
        Extract internal links with anchor text.

        Args:
            base_url: Base URL to determine internal links

        Returns:
            List of internal link data
        """
        from ..utils.url import same_host

        links = []
        anchor_tags = self.soup.find_all("a", href=True)

        for anchor in anchor_tags:
            href = anchor.get("href")
            absolute_url = urljoin(self.url, href)

            if same_host(absolute_url, base_url):
                links.append({
                    "url": absolute_url,
                    "anchor_text": anchor.get_text().strip(),
                    "title": anchor.get("title"),
                    "rel": anchor.get("rel"),
                })

        return links

    def extract_external_links(self, base_url: str) -> list[dict[str, str]]:
        """
        Extract external links with metadata.

        Args:
            base_url: Base URL to determine external links

        Returns:
            List of external link data
        """
        from ..utils.url import same_host

        links = []
        anchor_tags = self.soup.find_all("a", href=True)

        for anchor in anchor_tags:
            href = anchor.get("href")
            if href.startswith(("http://", "https://")):
                if not same_host(href, base_url):
                    links.append({
                        "url": href,
                        "anchor_text": anchor.get_text().strip(),
                        "rel": anchor.get("rel"),
                        "nofollow": "nofollow" in (anchor.get("rel") or []),
                    })

        return links


class HTMLParser:
    """Main parser combining structured data and content extraction."""

    def __init__(self, html: str, url: str):
        """
        Initialize the HTML parser.

        Args:
            html: HTML content to parse
            url: URL of the page
        """
        self.html = html
        self.url = url
        self.structured_data_parser = StructuredDataParser(html, url)
        self.content_parser = ContentParser(html, url)

    def parse_all(self) -> dict[str, Any]:
        """
        Parse all data from the HTML.

        Returns:
            Dictionary containing all parsed data
        """
        return {
            "url": self.url,
            "structured_data": self.structured_data_parser.extract_all(),
            "schema_types": self.structured_data_parser.get_schema_types(),
            "headings": self.content_parser.extract_headings(),
            "heading_issues": self.content_parser.validate_heading_hierarchy(),
            "images": self.content_parser.check_images_have_alt(),
            "word_count": self.content_parser.extract_word_count(),
        }
