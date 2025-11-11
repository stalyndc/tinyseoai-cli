"""
Scoring algorithms for SEO impact/effort analysis and health score calculation.
"""
from __future__ import annotations

from .models import Issue

# Impact scores for different issue types (1-10, higher = more impact)
ISSUE_IMPACT_SCORES = {
    # Critical SEO Issues (9-10)
    "no_https": 10,
    "duplicate_content": 10,
    "noindex_directive": 10,
    "ssl_expired": 10,
    "missing_viewport": 10,
    "render_blocking_javascript": 9,
    "multiple_canonical_tags": 9,
    "conflicting_robots_directives": 9,

    # High Impact (7-8)
    "title_missing": 8,
    "canonical_http_on_https": 8,
    "very_thin_content": 8,
    "missing_canonical": 7,
    "canonical_points_elsewhere": 7,
    "missing_og_tag": 7,
    "large_html_size": 7,
    "no_compression": 7,

    # Medium Impact (5-6)
    "title_too_long": 6,
    "meta_description_missing": 6,
    "missing_hsts": 6,
    "render_blocking_css": 6,
    "orphan_page": 6,
    "thin_content": 6,
    "potential_keyword_stuffing": 6,
    "near_duplicate_content": 6,
    "broken_link": 5,
    "missing_html_lang": 5,
    "images_without_dimensions": 5,
    "missing_csp": 5,

    # Low Impact (3-4)
    "duplicate_title": 4,
    "duplicate_meta_description": 4,
    "img_alt_missing": 4,
    "missing_twitter_card": 4,
    "missing_favicon": 4,
    "page_too_deep": 4,
    "empty_anchor_text": 3,
    "generic_anchor_text": 3,
    "missing_etag": 3,
    "long_sentences": 3,

    # Info/Minor (1-2)
    "nofollow_directive": 2,
    "noarchive_directive": 2,
    "missing_preconnect": 2,
    "compression_not_optimal": 2,
    "missing_twitter_site": 1,
    "missing_apple_touch_icon": 1,
    "complex_vocabulary": 1,
}


# Effort scores for fixing different issue types (1-10, higher = more effort)
ISSUE_EFFORT_SCORES = {
    # High Effort (8-10)
    "no_https": 9,  # Requires SSL certificate and configuration
    "duplicate_content": 8,  # May require content rewriting
    "orphan_page": 8,  # Requires site structure changes
    "page_too_deep": 7,  # Requires navigation restructuring
    "near_duplicate_content": 7,  # Content rewriting
    "potential_keyword_stuffing": 7,  # Content rewriting
    "thin_content": 7,  # Content creation
    "very_thin_content": 8,  # Significant content creation

    # Medium Effort (4-6)
    "render_blocking_javascript": 6,  # Code restructuring
    "render_blocking_css": 5,  # CSS optimization
    "large_html_size": 5,  # Code optimization
    "broken_link": 4,  # Find and fix or redirect
    "missing_canonical": 4,  # Template modification
    "missing_og_tag": 4,  # Template modification

    # Low Effort (1-3)
    "title_missing": 2,  # Add meta tag
    "title_too_long": 1,  # Edit text
    "meta_description_missing": 2,  # Add meta tag
    "duplicate_title": 2,  # Edit text
    "duplicate_meta_description": 2,  # Edit text
    "img_alt_missing": 2,  # Add attribute
    "missing_viewport": 1,  # Add meta tag
    "missing_html_lang": 1,  # Add attribute
    "no_compression": 3,  # Server configuration
    "missing_hsts": 2,  # Server configuration
    "missing_csp": 3,  # Server configuration
    "missing_favicon": 2,  # Upload file
    "missing_twitter_card": 2,  # Add meta tags
    "empty_anchor_text": 1,  # Edit text
    "generic_anchor_text": 1,  # Edit text
    "images_without_dimensions": 2,  # Add attributes
    "missing_preconnect": 1,  # Add link tag
    "missing_etag": 2,  # Server configuration
}


class IssueScorer:
    """Score issues based on impact and effort."""

    def __init__(self):
        """Initialize the issue scorer."""
        self.impact_scores = ISSUE_IMPACT_SCORES.copy()
        self.effort_scores = ISSUE_EFFORT_SCORES.copy()

    def get_impact_score(self, issue_type: str) -> int:
        """
        Get impact score for an issue type.

        Args:
            issue_type: Type of the issue

        Returns:
            Impact score (1-10)
        """
        return self.impact_scores.get(issue_type, 5)  # Default to medium impact

    def get_effort_score(self, issue_type: str) -> int:
        """
        Get effort score for an issue type.

        Args:
            issue_type: Type of the issue

        Returns:
            Effort score (1-10)
        """
        return self.effort_scores.get(issue_type, 5)  # Default to medium effort

    def get_priority_score(self, issue_type: str) -> float:
        """
        Calculate priority score (impact/effort ratio).

        Higher priority = high impact, low effort (quick wins).

        Args:
            issue_type: Type of the issue

        Returns:
            Priority score (0-10)
        """
        impact = self.get_impact_score(issue_type)
        effort = self.get_effort_score(issue_type)

        # Priority is impact divided by effort, scaled to 0-10
        # High impact + low effort = high priority
        priority = (impact / effort) * 5  # Scale factor
        return min(10.0, priority)  # Cap at 10

    def score_issue(self, issue: Issue) -> dict[str, any]:
        """
        Score a single issue.

        Args:
            issue: Issue to score

        Returns:
            Dictionary with scores
        """
        impact = self.get_impact_score(issue.type)
        effort = self.get_effort_score(issue.type)
        priority = self.get_priority_score(issue.type)

        # Adjust for severity
        severity_multipliers = {
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8,
            "info": 0.5,
        }
        multiplier = severity_multipliers.get(issue.severity, 1.0)

        return {
            "type": issue.type,
            "url": issue.url,
            "severity": issue.severity,
            "impact": round(impact * multiplier, 1),
            "effort": effort,
            "priority": round(priority * multiplier, 1),
            "category": self._categorize_issue(issue.type),
        }

    def _categorize_issue(self, issue_type: str) -> str:
        """Categorize issue into broad categories."""
        categories = {
            "content": [
                "title_missing",
                "title_too_long",
                "meta_description_missing",
                "duplicate_title",
                "duplicate_meta_description",
                "thin_content",
                "very_thin_content",
                "duplicate_content",
                "near_duplicate_content",
                "potential_keyword_stuffing",
            ],
            "technical": [
                "no_https",
                "ssl_expired",
                "missing_canonical",
                "multiple_canonical_tags",
                "noindex_directive",
                "conflicting_robots_directives",
                "missing_viewport",
            ],
            "links": [
                "broken_link",
                "orphan_page",
                "page_too_deep",
                "empty_anchor_text",
                "generic_anchor_text",
            ],
            "performance": [
                "large_html_size",
                "no_compression",
                "render_blocking_css",
                "render_blocking_javascript",
                "images_without_dimensions",
            ],
            "social": [
                "missing_og_tag",
                "missing_twitter_card",
                "missing_favicon",
            ],
            "security": [
                "no_https",
                "ssl_expired",
                "missing_hsts",
                "missing_csp",
            ],
        }

        for category, issue_types in categories.items():
            if issue_type in issue_types:
                return category

        return "other"


class HealthScoreCalculator:
    """Calculate overall SEO health score."""

    def __init__(self):
        """Initialize health score calculator."""
        self.scorer = IssueScorer()

    def calculate_health_score(
        self, issues: list[Issue], pages_scanned: int
    ) -> dict[str, any]:
        """
        Calculate overall SEO health score.

        Args:
            issues: List of issues found
            pages_scanned: Number of pages scanned

        Returns:
            Dictionary with health score and breakdown
        """
        if pages_scanned == 0:
            return {"overall_score": 0, "grade": "F"}

        # Score all issues
        scored_issues = [self.scorer.score_issue(issue) for issue in issues]

        # Calculate category scores
        category_scores = self._calculate_category_scores(scored_issues)

        # Calculate overall score (0-100)
        # Start with perfect score and deduct based on issues
        base_score = 100
        total_impact = sum(si["impact"] for si in scored_issues)

        # Penalty is proportional to total impact and number of pages
        # More pages with fewer issues per page = better score
        issue_density = len(issues) / pages_scanned if pages_scanned > 0 else 0
        impact_penalty = (total_impact / pages_scanned) * 2 if pages_scanned > 0 else total_impact

        overall_score = max(0, base_score - impact_penalty - (issue_density * 5))
        overall_score = round(overall_score, 1)

        # Assign letter grade
        grade = self._get_letter_grade(overall_score)

        return {
            "overall_score": overall_score,
            "grade": grade,
            "total_issues": len(issues),
            "pages_scanned": pages_scanned,
            "issues_per_page": round(issue_density, 2),
            "category_scores": category_scores,
            "critical_issues": sum(1 for i in issues if i.severity == "high"),
            "recommendations": self._generate_recommendations(scored_issues),
        }

    def _calculate_category_scores(
        self, scored_issues: list[dict[str, any]]
    ) -> dict[str, dict[str, any]]:
        """Calculate scores by category."""
        categories = {}

        for scored_issue in scored_issues:
            category = scored_issue["category"]
            if category not in categories:
                categories[category] = {
                    "count": 0,
                    "total_impact": 0,
                    "avg_impact": 0,
                    "avg_effort": 0,
                }

            categories[category]["count"] += 1
            categories[category]["total_impact"] += scored_issue["impact"]

        # Calculate averages
        for category, data in categories.items():
            if data["count"] > 0:
                category_issues = [
                    si for si in scored_issues if si["category"] == category
                ]
                data["avg_impact"] = round(data["total_impact"] / data["count"], 1)
                data["avg_effort"] = round(
                    sum(si["effort"] for si in category_issues) / len(category_issues), 1
                )

        return categories

    def _get_letter_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_recommendations(
        self, scored_issues: list[dict[str, any]]
    ) -> list[dict[str, any]]:
        """
        Generate top recommendations based on priority.

        Args:
            scored_issues: List of scored issues

        Returns:
            List of top recommendations
        """
        # Sort by priority (highest first)
        sorted_issues = sorted(
            scored_issues, key=lambda x: x["priority"], reverse=True
        )

        # Group by type and take top 10
        recommendations = []
        seen_types = set()

        for issue in sorted_issues:
            if issue["type"] not in seen_types:
                recommendations.append({
                    "issue_type": issue["type"],
                    "category": issue["category"],
                    "impact": issue["impact"],
                    "effort": issue["effort"],
                    "priority": issue["priority"],
                })
                seen_types.add(issue["type"])

            if len(recommendations) >= 10:
                break

        return recommendations


def prioritize_issues(issues: list[Issue]) -> list[tuple[Issue, dict[str, any]]]:
    """
    Prioritize issues by their impact/effort ratio.

    Args:
        issues: List of issues

    Returns:
        List of (issue, scores) tuples sorted by priority
    """
    scorer = IssueScorer()
    scored = [(issue, scorer.score_issue(issue)) for issue in issues]

    # Sort by priority (descending)
    scored.sort(key=lambda x: x[1]["priority"], reverse=True)

    return scored
