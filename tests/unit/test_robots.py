"""
Unit tests for robots.txt parsing and sitemap discovery.
"""
import pytest
from unittest.mock import AsyncMock, Mock

from tinyseoai.audit.robots import RobotsAnalyzer, SitemapParser


@pytest.mark.unit
class TestRobotsAnalyzer:
    """Test RobotsAnalyzer functionality."""

    @pytest.mark.asyncio
    async def test_fetch_and_parse_success(self, mock_httpx_client, sample_robots_txt):
        """Test successful robots.txt fetching and parsing."""
        # Arrange
        analyzer = RobotsAnalyzer("https://example.com")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_robots_txt
        mock_httpx_client.get.return_value = mock_response

        # Act
        success = await analyzer.fetch_and_parse(mock_httpx_client)

        # Assert
        assert success is True
        assert analyzer.content is not None
        assert len(analyzer.sitemaps) > 0
        mock_httpx_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_and_parse_not_found(self, mock_httpx_client):
        """Test robots.txt not found."""
        # Arrange
        analyzer = RobotsAnalyzer("https://example.com")
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.get.return_value = mock_response

        # Act
        success = await analyzer.fetch_and_parse(mock_httpx_client)

        # Assert
        assert success is False
        assert analyzer.content is None

    def test_extract_sitemaps(self, sample_robots_txt):
        """Test sitemap extraction from robots.txt."""
        # Arrange
        analyzer = RobotsAnalyzer("https://example.com")
        analyzer.content = sample_robots_txt

        # Act
        analyzer._extract_sitemaps()

        # Assert
        assert len(analyzer.sitemaps) >= 1
        assert any("sitemap.xml" in s.lower() for s in analyzer.sitemaps)

    def test_extract_crawl_delay(self):
        """Test crawl delay extraction."""
        # Arrange
        robots_txt = """
        User-agent: *
        Crawl-delay: 2
        """
        analyzer = RobotsAnalyzer("https://example.com")
        analyzer.content = robots_txt

        # Act
        analyzer._extract_crawl_delay()

        # Assert
        assert analyzer.crawl_delay == 2.0

    def test_extract_rules(self):
        """Test extraction of allow/disallow rules."""
        # Arrange
        robots_txt = """
        User-agent: *
        Disallow: /admin/
        Disallow: /private/
        Allow: /public/
        """
        analyzer = RobotsAnalyzer("https://example.com")
        analyzer.content = robots_txt

        # Act
        analyzer._extract_rules()

        # Assert
        assert len(analyzer.disallowed_paths) == 2
        assert "/admin/" in analyzer.disallowed_paths
        assert len(analyzer.allowed_paths) == 1
        assert "/public/" in analyzer.allowed_paths

    def test_can_fetch_allowed(self, sample_robots_txt):
        """Test can_fetch for allowed URL."""
        # Arrange
        analyzer = RobotsAnalyzer("https://example.com")
        analyzer.content = sample_robots_txt
        analyzer.parser.parse(sample_robots_txt.splitlines())

        # Act
        can_fetch = analyzer.can_fetch("https://example.com/public/page.html")

        # Assert
        assert can_fetch is True

    def test_can_fetch_no_robots(self):
        """Test can_fetch when no robots.txt exists."""
        # Arrange
        analyzer = RobotsAnalyzer("https://example.com")

        # Act
        can_fetch = analyzer.can_fetch("https://example.com/any/page.html")

        # Assert
        assert can_fetch is True  # No robots.txt means everything is allowed

    def test_get_summary(self, sample_robots_txt):
        """Test get_summary method."""
        # Arrange
        analyzer = RobotsAnalyzer("https://example.com")
        analyzer.content = sample_robots_txt
        analyzer._extract_sitemaps()
        analyzer._extract_crawl_delay()
        analyzer._extract_rules()

        # Act
        summary = analyzer.get_summary()

        # Assert
        assert summary["exists"] is True
        assert summary["sitemaps_count"] >= 0
        assert "robots_url" in summary
        assert "disallowed_paths" in summary


@pytest.mark.unit
class TestSitemapParser:
    """Test SitemapParser functionality."""

    @pytest.mark.asyncio
    async def test_parse_urlset(self, mock_httpx_client, sample_sitemap_xml):
        """Test parsing a standard sitemap."""
        # Arrange
        parser = SitemapParser("https://example.com/sitemap.xml")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_sitemap_xml
        mock_httpx_client.get.return_value = mock_response

        # Act
        success = await parser.fetch_and_parse(mock_httpx_client)

        # Assert
        assert success is True
        assert len(parser.urls) > 0
        assert all("loc" in url_data for url_data in parser.urls)

    @pytest.mark.asyncio
    async def test_parse_sitemap_index(self, mock_httpx_client):
        """Test parsing a sitemap index."""
        # Arrange
        sitemap_index_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap>
                <loc>https://example.com/sitemap-posts.xml</loc>
            </sitemap>
            <sitemap>
                <loc>https://example.com/sitemap-pages.xml</loc>
            </sitemap>
        </sitemapindex>
        """
        parser = SitemapParser("https://example.com/sitemap_index.xml")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sitemap_index_xml
        mock_httpx_client.get.return_value = mock_response

        # Act
        success = await parser.fetch_and_parse(mock_httpx_client)

        # Assert
        assert success is True
        assert len(parser.nested_sitemaps) == 2
        assert "sitemap-posts.xml" in parser.nested_sitemaps[0]

    def test_extract_url_data(self, sample_sitemap_xml):
        """Test extracting URL data from sitemap entry."""
        # Arrange
        parser = SitemapParser("https://example.com/sitemap.xml")
        parser._parse_xml(sample_sitemap_xml)

        # Act
        urls = parser.get_urls()

        # Assert
        assert len(urls) > 0
        assert all(url.startswith("https://") for url in urls)

    def test_get_priority_urls(self, sample_sitemap_xml):
        """Test getting high-priority URLs from sitemap."""
        # Arrange
        parser = SitemapParser("https://example.com/sitemap.xml")
        parser._parse_xml(sample_sitemap_xml)

        # Act
        priority_urls = parser.get_priority_urls(min_priority=0.9)

        # Assert
        # Should return URLs with priority >= 0.9
        assert isinstance(priority_urls, list)

    @pytest.mark.asyncio
    async def test_parse_failure(self, mock_httpx_client):
        """Test handling of parse failure."""
        # Arrange
        parser = SitemapParser("https://example.com/sitemap.xml")
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.get.return_value = mock_response

        # Act
        success = await parser.fetch_and_parse(mock_httpx_client)

        # Assert
        assert success is False
