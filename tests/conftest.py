"""
Pytest configuration and shared fixtures.
"""
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

import pytest
import httpx
from faker import Faker

from tinyseoai.config import AppConfig
from tinyseoai.data.models import Issue, AuditResult


# ==================== Session-scoped fixtures ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def faker_instance():
    """Provide a Faker instance for generating test data."""
    return Faker()


# ==================== Function-scoped fixtures ====================

@pytest.fixture
def mock_config() -> AppConfig:
    """Provide a mock application configuration."""
    return AppConfig(
        api_base="https://api.tinyseoai.com",
        plan="free",
        openai_model_free="gpt-4o-mini",
        openai_model_premium="gpt-5",
        max_output_tokens=800,
    )


@pytest.fixture
def sample_url(faker_instance: Faker) -> str:
    """Generate a sample URL for testing."""
    return "https://example.com"


@pytest.fixture
def sample_html() -> str:
    """Provide sample HTML for parsing tests."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page Title</title>
        <meta name="description" content="Test page description">
        <meta name="robots" content="index, follow">
    </head>
    <body>
        <h1>Welcome to Test Page</h1>
        <p>This is a test paragraph.</p>
        <a href="/page1">Internal Link 1</a>
        <a href="https://example.com/page2">Internal Link 2</a>
        <a href="https://external.com">External Link</a>
        <a href="#anchor">Anchor Link</a>
        <a href="javascript:void(0)">JavaScript Link</a>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_no_meta() -> str:
    """Provide sample HTML without meta tags."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
    </head>
    <body>
        <h1>Page Without Meta</h1>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_noindex() -> str:
    """Provide sample HTML with noindex directive."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>No Index Page</title>
        <meta name="robots" content="noindex, nofollow">
    </head>
    <body>
        <h1>This page should not be indexed</h1>
    </body>
    </html>
    """


@pytest.fixture
def sample_issues() -> list[Issue]:
    """Provide sample SEO issues for testing."""
    return [
        Issue(
            url="https://example.com/page1",
            type="title_missing",
            severity="medium",
        ),
        Issue(
            url="https://example.com/page2",
            type="title_too_long",
            severity="low",
            detail="75",
        ),
        Issue(
            url="https://example.com/page3",
            type="meta_description_missing",
            severity="low",
        ),
        Issue(
            url="https://example.com/page4",
            type="broken_link",
            severity="medium",
            detail="https://example.com/404",
        ),
        Issue(
            url="https://example.com/page5",
            type="duplicate_title",
            severity="low",
            detail="Duplicate Title",
        ),
    ]


@pytest.fixture
def sample_audit_result(sample_issues: list[Issue]) -> AuditResult:
    """Provide a sample audit result for testing."""
    return AuditResult(
        site="https://example.com",
        pages_scanned=10,
        issues=sample_issues,
        meta={
            "max_pages": 50,
            "timestamp": "2025-01-15T10:30:00Z",
            "agent": "tinyseoai/0.1.0",
        },
    )


@pytest.fixture
async def mock_httpx_client() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mocked httpx AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    yield client


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    def _create_response(
        status_code: int = 200,
        text: str = "",
        content_type: str = "text/html",
    ):
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.text = text
        response.headers = {"content-type": content_type}
        return response

    return _create_response


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def sample_robots_txt() -> str:
    """Provide sample robots.txt content."""
    return """
User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /public/

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-news.xml
Crawl-delay: 1
"""


@pytest.fixture
def sample_sitemap_xml() -> str:
    """Provide sample sitemap.xml content."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>2025-01-01</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://example.com/about</loc>
        <lastmod>2025-01-05</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://example.com/blog</loc>
        <lastmod>2025-01-10</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
</urlset>
"""


# ==================== AI/LLM fixtures ====================

@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    def _create_response(content: str):
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = content
        return response

    return _create_response


@pytest.fixture
def sample_ai_summary() -> dict:
    """Provide a sample AI-generated summary."""
    return {
        "site": "https://example.com",
        "summary": "The website has several SEO issues that need attention. "
        "Focus on fixing missing titles and meta descriptions first.",
        "top_issues": [
            {
                "type": "title_missing",
                "count": 5,
                "impact": "high",
                "priority": 1,
            },
            {
                "type": "meta_description_missing",
                "count": 8,
                "impact": "medium",
                "priority": 2,
            },
        ],
        "recommended_actions": [
            {
                "action": "Add title tags to all pages",
                "impact": "high",
                "effort": "low",
                "priority": 1,
            },
            {
                "action": "Write unique meta descriptions",
                "impact": "medium",
                "effort": "medium",
                "priority": 2,
            },
        ],
        "quick_wins": [
            "Fix missing title tags (5 pages)",
            "Add alt text to images",
            "Fix broken internal links",
        ],
    }


# ==================== Markers ====================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line("markers", "slow: mark test as slow-running")
    config.addinivalue_line("markers", "ai: mark test as requiring AI API")
    config.addinivalue_line("markers", "network: mark test as requiring network")
