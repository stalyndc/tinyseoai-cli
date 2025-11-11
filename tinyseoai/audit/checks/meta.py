"""
Meta tag validation including Open Graph, Twitter Cards, and other social meta tags.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from loguru import logger

from ...data.models import Issue


class MetaTagChecker:
    """Check and validate meta tags for SEO and social sharing."""

    def __init__(self, html: str, url: str):
        """
        Initialize the meta tag checker.

        Args:
            html: HTML content to check
            url: URL of the page
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, "lxml")

    def check_all(self) -> List[Issue]:
        """
        Run all meta tag checks.

        Returns:
            List of issues found
        """
        issues = []

        issues.extend(self.check_basic_meta())
        issues.extend(self.check_open_graph())
        issues.extend(self.check_twitter_cards())
        issues.extend(self.check_favicon())
        issues.extend(self.check_language())
        issues.extend(self.check_viewport())

        return issues

    def check_basic_meta(self) -> List[Issue]:
        """
        Check basic meta tags.

        Returns:
            List of basic meta tag issues
        """
        issues = []

        # These are checked in the main crawler, but we can add validation
        charset = self.soup.find("meta", attrs={"charset": True})
        if not charset:
            # Check for http-equiv charset
            http_equiv_charset = self.soup.find(
                "meta", attrs={"http-equiv": "Content-Type"}
            )
            if not http_equiv_charset:
                issues.append(
                    Issue(
                        url=self.url,
                        type="missing_charset",
                        severity="low",
                        detail="No charset meta tag found. Should declare UTF-8.",
                    )
                )

        return issues

    def check_open_graph(self) -> List[Issue]:
        """
        Check Open Graph meta tags for social sharing.

        Returns:
            List of Open Graph issues
        """
        issues = []

        # Required OG tags
        required_og_tags = {
            "og:title": "Open Graph title",
            "og:type": "Open Graph type",
            "og:image": "Open Graph image",
            "og:url": "Open Graph URL",
        }

        # Optional but recommended
        recommended_og_tags = {
            "og:description": "Open Graph description",
            "og:site_name": "Open Graph site name",
        }

        # Check required tags
        for property_name, display_name in required_og_tags.items():
            og_tag = self.soup.find("meta", property=property_name)
            if not og_tag or not og_tag.get("content"):
                issues.append(
                    Issue(
                        url=self.url,
                        type="missing_og_tag",
                        severity="medium",
                        detail=f"Missing required {display_name} ({property_name})",
                    )
                )

        # Check recommended tags
        for property_name, display_name in recommended_og_tags.items():
            og_tag = self.soup.find("meta", property=property_name)
            if not og_tag or not og_tag.get("content"):
                issues.append(
                    Issue(
                        url=self.url,
                        type="missing_recommended_og_tag",
                        severity="low",
                        detail=f"Missing recommended {display_name} ({property_name})",
                    )
                )

        # Validate OG image
        og_image = self.soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image.get("content")

            # Check if image URL is absolute
            if not image_url.startswith(("http://", "https://")):
                issues.append(
                    Issue(
                        url=self.url,
                        type="og_image_not_absolute",
                        severity="medium",
                        detail="Open Graph image URL should be absolute (include full URL)",
                    )
                )

            # Check for OG image dimensions
            og_image_width = self.soup.find("meta", property="og:image:width")
            og_image_height = self.soup.find("meta", property="og:image:height")

            if not og_image_width or not og_image_height:
                issues.append(
                    Issue(
                        url=self.url,
                        type="missing_og_image_dimensions",
                        severity="low",
                        detail="Missing og:image:width and og:image:height for better social sharing",
                    )
                )

        return issues

    def check_twitter_cards(self) -> List[Issue]:
        """
        Check Twitter Card meta tags.

        Returns:
            List of Twitter Card issues
        """
        issues = []

        twitter_card = self.soup.find("meta", attrs={"name": "twitter:card"})

        if not twitter_card or not twitter_card.get("content"):
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_twitter_card",
                    severity="low",
                    detail="Missing twitter:card meta tag. "
                    "This controls how content is displayed when shared on Twitter/X.",
                )
            )
        else:
            card_type = twitter_card.get("content")

            # Validate card type
            valid_card_types = [
                "summary",
                "summary_large_image",
                "app",
                "player",
            ]
            if card_type not in valid_card_types:
                issues.append(
                    Issue(
                        url=self.url,
                        type="invalid_twitter_card_type",
                        severity="medium",
                        detail=f"Invalid twitter:card type '{card_type}'. "
                        f"Should be one of: {', '.join(valid_card_types)}",
                    )
                )

            # Check for recommended Twitter tags based on card type
            if card_type in ["summary", "summary_large_image"]:
                twitter_title = self.soup.find("meta", attrs={"name": "twitter:title"})
                twitter_description = self.soup.find(
                    "meta", attrs={"name": "twitter:description"}
                )

                if not twitter_title or not twitter_title.get("content"):
                    # Twitter falls back to OG tags, but explicit is better
                    issues.append(
                        Issue(
                            url=self.url,
                            type="missing_twitter_title",
                            severity="info",
                            detail="Missing twitter:title. Falls back to og:title if available.",
                        )
                    )

                if not twitter_description or not twitter_description.get("content"):
                    issues.append(
                        Issue(
                            url=self.url,
                            type="missing_twitter_description",
                            severity="info",
                            detail="Missing twitter:description. "
                            "Falls back to og:description if available.",
                        )
                    )

                if card_type == "summary_large_image":
                    twitter_image = self.soup.find(
                        "meta", attrs={"name": "twitter:image"}
                    )
                    if not twitter_image or not twitter_image.get("content"):
                        issues.append(
                            Issue(
                                url=self.url,
                                type="missing_twitter_image",
                                severity="medium",
                                detail="Missing twitter:image for summary_large_image card type",
                            )
                        )

        # Check for Twitter site/creator
        twitter_site = self.soup.find("meta", attrs={"name": "twitter:site"})
        if not twitter_site or not twitter_site.get("content"):
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_twitter_site",
                    severity="info",
                    detail="Missing twitter:site meta tag. "
                    "This should be your Twitter/X username.",
                )
            )

        return issues

    def check_favicon(self) -> List[Issue]:
        """
        Check for favicon presence.

        Returns:
            List of favicon issues
        """
        issues = []

        # Check for various favicon formats
        favicon_found = False

        # Standard link rel="icon"
        icon_link = self.soup.find("link", rel=lambda r: r and "icon" in r.lower())
        if icon_link:
            favicon_found = True

        # Apple touch icon
        apple_icon = self.soup.find(
            "link", rel=lambda r: r and "apple-touch-icon" in r.lower()
        )

        if not favicon_found:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_favicon",
                    severity="low",
                    detail="No favicon found. Favicons improve brand recognition in browser tabs.",
                )
            )

        if not apple_icon:
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_apple_touch_icon",
                    severity="info",
                    detail="Missing apple-touch-icon for iOS home screen bookmarks",
                )
            )

        return issues

    def check_language(self) -> List[Issue]:
        """
        Check for language declaration.

        Returns:
            List of language-related issues
        """
        issues = []

        html_tag = self.soup.find("html")

        if not html_tag or not html_tag.get("lang"):
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_html_lang",
                    severity="medium",
                    detail="Missing lang attribute on <html> tag. "
                    "This helps search engines and accessibility tools.",
                )
            )

        # Check for hreflang tags (for international sites)
        hreflang_tags = self.soup.find_all("link", rel="alternate", hreflang=True)

        if len(hreflang_tags) > 0:
            # If using hreflang, should have x-default
            has_x_default = any(
                tag.get("hreflang") == "x-default" for tag in hreflang_tags
            )

            if not has_x_default:
                issues.append(
                    Issue(
                        url=self.url,
                        type="missing_hreflang_x_default",
                        severity="low",
                        detail="Using hreflang but missing x-default tag for fallback",
                    )
                )

        return issues

    def check_viewport(self) -> List[Issue]:
        """
        Check for viewport meta tag (mobile optimization).

        Returns:
            List of viewport issues
        """
        issues = []

        viewport = self.soup.find("meta", attrs={"name": "viewport"})

        if not viewport or not viewport.get("content"):
            issues.append(
                Issue(
                    url=self.url,
                    type="missing_viewport",
                    severity="high",
                    detail="Missing viewport meta tag. Critical for mobile responsiveness.",
                )
            )
        else:
            content = viewport.get("content", "").lower()

            # Check for recommended viewport settings
            if "width=device-width" not in content:
                issues.append(
                    Issue(
                        url=self.url,
                        type="viewport_missing_device_width",
                        severity="medium",
                        detail="Viewport should include width=device-width for proper mobile scaling",
                    )
                )

            if "initial-scale=1" not in content:
                issues.append(
                    Issue(
                        url=self.url,
                        type="viewport_missing_initial_scale",
                        severity="low",
                        detail="Viewport should include initial-scale=1 for proper mobile scaling",
                    )
                )

        return issues

    def get_meta_summary(self) -> Dict[str, any]:
        """
        Get a summary of all meta tags found.

        Returns:
            Dictionary with meta tag summary
        """
        summary = {
            "has_og_tags": bool(self.soup.find("meta", property=lambda p: p and p.startswith("og:"))),
            "has_twitter_cards": bool(self.soup.find("meta", attrs={"name": lambda n: n and n.startswith("twitter:")})),
            "has_favicon": bool(self.soup.find("link", rel=lambda r: r and "icon" in r.lower())),
            "has_viewport": bool(self.soup.find("meta", attrs={"name": "viewport"})),
            "has_lang": bool(self.soup.find("html", lang=True)),
            "og_tags_count": len(self.soup.find_all("meta", property=lambda p: p and p.startswith("og:"))),
            "twitter_tags_count": len(self.soup.find_all("meta", attrs={"name": lambda n: n and n.startswith("twitter:")})),
        }

        return summary
