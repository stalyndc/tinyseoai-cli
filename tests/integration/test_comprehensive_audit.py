"""
Integration tests for comprehensive audit functionality.
"""
import pytest

from tinyseoai.audit.engine_v2 import comprehensive_audit


@pytest.mark.integration
@pytest.mark.network
@pytest.mark.asyncio
async def test_comprehensive_audit_example_com():
    """Test comprehensive audit on example.com."""
    # Arrange
    url = "https://example.com"
    max_pages = 5  # Small number for faster testing

    # Act
    result = await comprehensive_audit(url, max_pages=max_pages, enable_all_checks=True)

    # Assert
    assert result is not None
    assert result.site == url
    assert result.pages_scanned > 0
    assert result.pages_scanned <= max_pages

    # Check that we have issues (example.com is simple but should have some)
    assert isinstance(result.issues, list)

    # Check metadata
    assert "health_score" in result.meta
    assert "health_grade" in result.meta
    assert 0 <= result.meta["health_score"] <= 100
    assert result.meta["health_grade"] in ["A", "B", "C", "D", "F"]

    # Check for robots.txt info
    assert "robots_txt_exists" in result.meta

    print(f"\n✓ Audit completed successfully!")
    print(f"  Pages scanned: {result.pages_scanned}")
    print(f"  Issues found: {len(result.issues)}")
    print(f"  Health score: {result.meta['health_score']}/100 ({result.meta['health_grade']})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fast_audit_mode():
    """Test fast audit mode (basic checks only)."""
    # Arrange
    url = "https://example.com"
    max_pages = 3

    # Act
    result = await comprehensive_audit(url, max_pages=max_pages, enable_all_checks=False)

    # Assert
    assert result is not None
    assert result.pages_scanned > 0
    assert isinstance(result.issues, list)

    print(f"\n✓ Fast audit completed!")
    print(f"  Pages scanned: {result.pages_scanned}")
    print(f"  Issues found: {len(result.issues)}")


@pytest.mark.integration
@pytest.mark.network
@pytest.mark.asyncio
async def test_audit_with_https_site():
    """Test audit on a well-configured HTTPS site."""
    # Arrange
    url = "https://www.mozilla.org"  # Known well-configured site
    max_pages = 5

    # Act
    result = await comprehensive_audit(url, max_pages=max_pages, enable_all_checks=True)

    # Assert
    assert result is not None
    assert result.pages_scanned > 0

    # Mozilla should have good security
    security_issues = [i for i in result.issues if "https" in i.type.lower() or "ssl" in i.type.lower()]

    # Check health score
    assert "health_score" in result.meta
    print(f"\n✓ Mozilla audit completed!")
    print(f"  Pages scanned: {result.pages_scanned}")
    print(f"  Health score: {result.meta['health_score']}/100")
    print(f"  Security issues: {len(security_issues)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_categorizes_issues():
    """Test that audit properly categorizes issues."""
    # Arrange
    url = "https://example.com"
    max_pages = 3

    # Act
    result = await comprehensive_audit(url, max_pages=max_pages, enable_all_checks=True)

    # Assert
    if "category_scores" in result.meta:
        category_scores = result.meta["category_scores"]
        assert isinstance(category_scores, dict)

        # Check that categories have proper structure
        for category, data in category_scores.items():
            assert "count" in data
            assert "total_impact" in data
            assert data["count"] > 0

        print(f"\n✓ Issue categorization working!")
        print(f"  Categories found: {list(category_scores.keys())}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_generates_recommendations():
    """Test that audit generates prioritized recommendations."""
    # Arrange
    url = "https://example.com"
    max_pages = 5

    # Act
    result = await comprehensive_audit(url, max_pages=max_pages, enable_all_checks=True)

    # Assert
    if "top_recommendations" in result.meta:
        recommendations = result.meta["top_recommendations"]
        assert isinstance(recommendations, list)

        if len(recommendations) > 0:
            # Check recommendation structure
            for rec in recommendations:
                assert "issue_type" in rec
                assert "impact" in rec
                assert "effort" in rec
                assert "priority" in rec
                assert rec["impact"] > 0
                assert rec["effort"] > 0

            # Recommendations should be sorted by priority
            priorities = [r["priority"] for r in recommendations]
            assert priorities == sorted(priorities, reverse=True)

            print(f"\n✓ Recommendations generated!")
            print(f"  Top recommendation: {recommendations[0]['issue_type']}")
            print(f"  Priority: {recommendations[0]['priority']:.1f}")
