"""
Unit tests for scoring algorithms.
"""
import pytest

from tinyseoai.data.models import Issue
from tinyseoai.data.scoring import (
    IssueScorer,
    HealthScoreCalculator,
    prioritize_issues,
    ISSUE_IMPACT_SCORES,
    ISSUE_EFFORT_SCORES,
)


@pytest.mark.unit
class TestIssueScorer:
    """Test IssueScorer functionality."""

    def test_get_impact_score_known_issue(self):
        """Test getting impact score for a known issue type."""
        # Arrange
        scorer = IssueScorer()

        # Act
        score = scorer.get_impact_score("no_https")

        # Assert
        assert score == ISSUE_IMPACT_SCORES["no_https"]
        assert score > 0

    def test_get_impact_score_unknown_issue(self):
        """Test getting impact score for unknown issue type."""
        # Arrange
        scorer = IssueScorer()

        # Act
        score = scorer.get_impact_score("unknown_issue_type")

        # Assert
        assert score == 5  # Default medium impact

    def test_get_effort_score_known_issue(self):
        """Test getting effort score for a known issue type."""
        # Arrange
        scorer = IssueScorer()

        # Act
        score = scorer.get_effort_score("title_missing")

        # Assert
        assert score == ISSUE_EFFORT_SCORES["title_missing"]
        assert score > 0

    def test_get_priority_score(self):
        """Test priority score calculation."""
        # Arrange
        scorer = IssueScorer()

        # Act
        # title_missing has high impact (8) and low effort (2)
        # So it should have high priority
        priority = scorer.get_priority_score("title_missing")

        # Assert
        assert priority > 0
        assert priority <= 10  # Should be capped at 10

    def test_priority_high_impact_low_effort(self):
        """Test that high impact + low effort = high priority."""
        # Arrange
        scorer = IssueScorer()

        # Act
        high_priority = scorer.get_priority_score("title_missing")  # High impact, low effort
        low_priority = scorer.get_priority_score("no_https")  # High impact, high effort

        # Assert
        assert high_priority > low_priority

    def test_score_issue(self):
        """Test scoring a full issue."""
        # Arrange
        scorer = IssueScorer()
        issue = Issue(
            url="https://example.com",
            type="title_missing",
            severity="medium",
        )

        # Act
        scored = scorer.score_issue(issue)

        # Assert
        assert "type" in scored
        assert "impact" in scored
        assert "effort" in scored
        assert "priority" in scored
        assert "category" in scored
        assert scored["type"] == "title_missing"

    def test_score_issue_with_severity_multiplier(self):
        """Test that severity affects scoring."""
        # Arrange
        scorer = IssueScorer()
        high_severity = Issue(url="https://example.com", type="broken_link", severity="high")
        low_severity = Issue(url="https://example.com", type="broken_link", severity="low")

        # Act
        high_scored = scorer.score_issue(high_severity)
        low_scored = scorer.score_issue(low_severity)

        # Assert
        assert high_scored["impact"] > low_scored["impact"]

    def test_categorize_issue_content(self):
        """Test categorizing content issues."""
        # Arrange
        scorer = IssueScorer()

        # Act
        category = scorer._categorize_issue("title_missing")

        # Assert
        assert category == "content"

    def test_categorize_issue_technical(self):
        """Test categorizing technical issues."""
        # Arrange
        scorer = IssueScorer()

        # Act
        category = scorer._categorize_issue("no_https")

        # Assert
        assert category in ["technical", "security"]  # Can be in either

    def test_categorize_issue_unknown(self):
        """Test categorizing unknown issues."""
        # Arrange
        scorer = IssueScorer()

        # Act
        category = scorer._categorize_issue("totally_unknown_issue")

        # Assert
        assert category == "other"


@pytest.mark.unit
class TestHealthScoreCalculator:
    """Test HealthScoreCalculator functionality."""

    def test_calculate_health_score_perfect(self):
        """Test health score for site with no issues."""
        # Arrange
        calculator = HealthScoreCalculator()
        issues = []
        pages_scanned = 10

        # Act
        result = calculator.calculate_health_score(issues, pages_scanned)

        # Assert
        assert result["overall_score"] == 100
        assert result["grade"] == "A"
        assert result["total_issues"] == 0
        assert result["critical_issues"] == 0

    def test_calculate_health_score_with_issues(self, sample_issues):
        """Test health score with various issues."""
        # Arrange
        calculator = HealthScoreCalculator()
        pages_scanned = 10

        # Act
        result = calculator.calculate_health_score(sample_issues, pages_scanned)

        # Assert
        assert 0 <= result["overall_score"] <= 100
        assert result["grade"] in ["A", "B", "C", "D", "F"]
        assert result["total_issues"] == len(sample_issues)
        assert result["pages_scanned"] == pages_scanned
        assert "category_scores" in result
        assert "recommendations" in result

    def test_get_letter_grade(self):
        """Test letter grade assignment."""
        # Arrange
        calculator = HealthScoreCalculator()

        # Act & Assert
        assert calculator._get_letter_grade(95) == "A"
        assert calculator._get_letter_grade(85) == "B"
        assert calculator._get_letter_grade(75) == "C"
        assert calculator._get_letter_grade(65) == "D"
        assert calculator._get_letter_grade(50) == "F"

    def test_calculate_category_scores(self):
        """Test category score calculation."""
        # Arrange
        calculator = HealthScoreCalculator()
        issues = [
            Issue(url="https://example.com", type="title_missing", severity="medium"),
            Issue(url="https://example.com", type="meta_description_missing", severity="low"),
            Issue(url="https://example.com", type="broken_link", severity="medium"),
        ]
        scored_issues = [calculator.scorer.score_issue(issue) for issue in issues]

        # Act
        category_scores = calculator._calculate_category_scores(scored_issues)

        # Assert
        assert "content" in category_scores
        assert "links" in category_scores
        assert category_scores["content"]["count"] == 2  # title and meta
        assert category_scores["links"]["count"] == 1  # broken link

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Arrange
        calculator = HealthScoreCalculator()
        issues = [
            Issue(url="https://example.com", type="title_missing", severity="high"),
            Issue(url="https://example.com", type="broken_link", severity="medium"),
            Issue(url="https://example.com", type="missing_favicon", severity="low"),
        ]
        scored_issues = [calculator.scorer.score_issue(issue) for issue in issues]

        # Act
        recommendations = calculator._generate_recommendations(scored_issues)

        # Assert
        assert len(recommendations) > 0
        assert len(recommendations) <= 10
        # Recommendations should be sorted by priority
        assert all("priority" in rec for rec in recommendations)

    def test_health_score_zero_pages(self):
        """Test health score with zero pages scanned."""
        # Arrange
        calculator = HealthScoreCalculator()
        issues = []

        # Act
        result = calculator.calculate_health_score(issues, 0)

        # Assert
        assert result["overall_score"] == 0
        assert result["grade"] == "F"


@pytest.mark.unit
def test_prioritize_issues(sample_issues):
    """Test issue prioritization."""
    # Act
    prioritized = prioritize_issues(sample_issues)

    # Assert
    assert len(prioritized) == len(sample_issues)
    assert all(isinstance(item, tuple) for item in prioritized)
    assert all(len(item) == 2 for item in prioritized)

    # Check that first item has highest priority
    priorities = [item[1]["priority"] for item in prioritized]
    assert priorities == sorted(priorities, reverse=True)


@pytest.mark.unit
def test_quick_wins_identified():
    """Test that quick wins (high impact, low effort) are prioritized."""
    # Arrange
    issues = [
        Issue(url="https://example.com", type="title_missing", severity="medium"),  # High impact, low effort
        Issue(url="https://example.com", type="no_https", severity="high"),  # High impact, high effort
    ]

    # Act
    prioritized = prioritize_issues(issues)

    # Assert
    # title_missing should be higher priority than no_https
    first_issue_type = prioritized[0][0].type
    assert first_issue_type == "title_missing"
