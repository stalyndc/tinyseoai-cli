"""
Unit tests for the crawler module.
"""
import pytest
from unittest.mock import AsyncMock
import httpx

from tinyseoai.audit.crawler import fetch_page, extract_links, extract_meta


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_page_success(mock_httpx_client, mock_response, sample_html):
    """Test successful page fetch."""
    # Arrange
    url = "https://example.com"
    mock_resp = mock_response(status_code=200, text=sample_html)
    mock_httpx_client.get.return_value = mock_resp

    # Act
    response = await fetch_page(mock_httpx_client, url)

    # Assert
    assert response is not None
    assert response.status_code == 200
    assert response.text == sample_html
    mock_httpx_client.get.assert_called_once_with(
        url, timeout=15.0, follow_redirects=True
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_page_failure(mock_httpx_client):
    """Test page fetch failure."""
    # Arrange
    url = "https://example.com"
    mock_httpx_client.get.side_effect = httpx.TimeoutException("Timeout")

    # Act
    response = await fetch_page(mock_httpx_client, url)

    # Assert
    assert response is None


@pytest.mark.unit
def test_extract_links(sample_html):
    """Test link extraction from HTML."""
    # Arrange
    base_url = "https://example.com"

    # Act
    links = extract_links(sample_html, base_url)

    # Assert
    assert isinstance(links, set)
    assert len(links) > 0
    # Should include internal links
    assert "https://example.com/page1" in links
    assert "https://example.com/page2" in links
    # Should include external links
    assert "https://external.com/" in links  # Note: normalized
    # Should NOT include anchor links
    assert "https://example.com#anchor" not in links
    # Should NOT include javascript links
    assert not any("javascript:" in link for link in links)


@pytest.mark.unit
def test_extract_links_empty_html():
    """Test link extraction from empty HTML."""
    # Arrange
    html = "<html><body></body></html>"
    base_url = "https://example.com"

    # Act
    links = extract_links(html, base_url)

    # Assert
    assert isinstance(links, set)
    assert len(links) == 0


@pytest.mark.unit
def test_extract_meta_complete(sample_html):
    """Test metadata extraction from complete HTML."""
    # Act
    title, meta_desc, noindex = extract_meta(sample_html)

    # Assert
    assert title == "Test Page Title"
    assert meta_desc == "Test page description"
    assert noindex is False


@pytest.mark.unit
def test_extract_meta_missing(sample_html_no_meta):
    """Test metadata extraction from HTML without meta tags."""
    # Act
    title, meta_desc, noindex = extract_meta(sample_html_no_meta)

    # Assert
    assert title is None
    assert meta_desc is None
    assert noindex is False


@pytest.mark.unit
def test_extract_meta_noindex(sample_html_noindex):
    """Test metadata extraction with noindex directive."""
    # Act
    title, meta_desc, noindex = extract_meta(sample_html_noindex)

    # Assert
    assert title == "No Index Page"
    assert meta_desc is None
    assert noindex is True


@pytest.mark.unit
def test_extract_meta_robots_case_insensitive():
    """Test that robots meta tag is detected case-insensitively."""
    # Arrange
    html = """
    <html>
    <head>
        <meta name="ROBOTS" content="NOINDEX">
    </head>
    </html>
    """

    # Act
    _, _, noindex = extract_meta(html)

    # Assert
    assert noindex is True
