"""
Custom exceptions for TinySEO AI.
"""


class TinySEOError(Exception):
    """Base exception for all TinySEO AI errors."""

    pass


class CrawlerError(TinySEOError):
    """Raised when crawling fails."""

    pass


class ParserError(TinySEOError):
    """Raised when parsing HTML content fails."""

    pass


class AIError(TinySEOError):
    """Raised when AI/LLM operations fail."""

    pass


class ValidationError(TinySEOError):
    """Raised when data validation fails."""

    pass


class ConfigError(TinySEOError):
    """Raised when configuration is invalid."""

    pass


class ReportError(TinySEOError):
    """Raised when report generation fails."""

    pass


class AuditError(TinySEOError):
    """Raised when audit operations fail."""

    pass
