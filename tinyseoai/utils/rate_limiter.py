from __future__ import annotations

import asyncio
import time
from typing import Optional


class RateLimiter:
    """
    Simple async rate limiter used to throttle crawler requests.

    Supports a base requests-per-second value and optionally honors a
    robots.txt crawl-delay directive when present.
    """

    def __init__(self, requests_per_second: float = 2.0, crawl_delay: float | None = None):
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than zero")

        self.requests_per_second = requests_per_second
        self._min_interval = 1.0 / requests_per_second
        self._crawl_delay = self._sanitize_delay(crawl_delay)
        self._lock = asyncio.Lock()
        self._last_request: float | None = None

    @staticmethod
    def _sanitize_delay(delay: float | None) -> float | None:
        if delay is None:
            return None
        return max(0.0, float(delay))

    def set_crawl_delay(self, delay: float | None) -> None:
        """Update crawl-delay at runtime (e.g., after parsing robots.txt)."""
        self._crawl_delay = self._sanitize_delay(delay)

    @property
    def effective_interval(self) -> float:
        """Return the greater of the base interval and crawl-delay."""
        if self._crawl_delay is not None and self._crawl_delay > 0:
            return max(self._min_interval, self._crawl_delay)
        return self._min_interval

    async def wait(self) -> None:
        """
        Await until the next request is allowed.

        The first call returns immediately. Subsequent calls enforce the
        configured interval, serialized via an async lock so multiple tasks
        share the same schedule.
        """
        async with self._lock:
            now = time.monotonic()
            if self._last_request is None:
                self._last_request = now
                return

            elapsed = now - self._last_request
            interval = self.effective_interval
            remaining = interval - elapsed
            if remaining > 0:
                await asyncio.sleep(remaining)
                now = time.monotonic()

            self._last_request = now
