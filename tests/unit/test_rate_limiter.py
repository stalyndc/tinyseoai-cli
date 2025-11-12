import time

import pytest

from tinyseoai.utils.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_enforces_min_interval():
    limiter = RateLimiter(requests_per_second=20)  # 0.05s interval

    await limiter.wait()
    first = time.monotonic()
    await limiter.wait()
    second = time.monotonic()

    assert second - first >= 0.045  # allow slight scheduling drift


@pytest.mark.asyncio
async def test_rate_limiter_respects_crawl_delay():
    limiter = RateLimiter(requests_per_second=50, crawl_delay=0.2)

    await limiter.wait()
    start = time.monotonic()
    await limiter.wait()
    elapsed = time.monotonic() - start

    assert elapsed >= 0.19


@pytest.mark.asyncio
async def test_rate_limiter_updates_delay_dynamically():
    limiter = RateLimiter(requests_per_second=10)  # 0.1s

    await limiter.wait()
    await limiter.wait()

    limiter.set_crawl_delay(0.3)
    start = time.monotonic()
    await limiter.wait()
    elapsed = time.monotonic() - start

    assert elapsed >= 0.29
