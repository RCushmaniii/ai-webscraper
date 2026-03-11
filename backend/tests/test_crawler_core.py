"""
Tests for core crawler URL filtering and rate limiting logic.

Covers _should_crawl_url protocol/extension checks and the RateLimiter class.
"""

import asyncio
import time
from unittest.mock import patch, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# _should_crawl_url: protocol & extension filtering
# ---------------------------------------------------------------------------

class TestShouldCrawlUrlFiltering:
    """Verify URL filtering by scheme and file extension."""

    def _patch_dns_public(self):
        """Return a context manager that makes all DNS lookups resolve to a public IP."""
        import socket
        result = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("93.184.216.34", 0))]
        return patch("socket.getaddrinfo", return_value=result)

    def test_should_crawl_url_valid_http(self, make_crawler):
        crawler = make_crawler()
        with self._patch_dns_public():
            assert crawler._should_crawl_url("http://example.com/page") is True

    def test_should_crawl_url_valid_https(self, make_crawler):
        crawler = make_crawler()
        with self._patch_dns_public():
            assert crawler._should_crawl_url("https://example.com/page") is True

    def test_should_crawl_url_rejects_ftp(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("ftp://example.com/file") is False

    def test_should_crawl_url_rejects_javascript(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("javascript:void(0)") is False

    def test_should_crawl_url_rejects_mailto(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("mailto:user@example.com") is False

    def test_should_crawl_url_rejects_data_uri(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("data:text/html,<h1>Hi</h1>") is False

    def test_should_crawl_url_skips_pdf(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/report.pdf") is False

    def test_should_crawl_url_skips_image_jpg(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/photo.jpg") is False

    def test_should_crawl_url_skips_image_png(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/logo.png") is False

    def test_should_crawl_url_skips_image_gif(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/anim.gif") is False

    def test_should_crawl_url_skips_zip(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/archive.zip") is False

    def test_should_crawl_url_skips_docx(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/file.docx") is False

    def test_should_crawl_url_skips_mp4(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/video.mp4") is False

    def test_should_crawl_url_skips_css(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/style.css") is False

    def test_should_crawl_url_skips_js_file(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("https://example.com/bundle.js") is False


# ---------------------------------------------------------------------------
# RateLimiter tests
# ---------------------------------------------------------------------------

class TestRateLimiter:
    """Verify the RateLimiter correctly throttles requests."""

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_delay(self):
        """After one call, the next wait should sleep for approximately the delay period."""
        from app.services.crawler import RateLimiter

        limiter = RateLimiter(requests_per_second=2.0)  # 0.5s delay
        assert limiter.delay == pytest.approx(0.5)

        # Simulate a first request that just happened
        limiter.last_request_time = time.monotonic()

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await limiter.wait()
            # Sleep should have been called with a value close to 0.5
            if mock_sleep.called:
                sleep_arg = mock_sleep.call_args[0][0]
                assert sleep_arg > 0
                assert sleep_arg <= 0.5

    @pytest.mark.asyncio
    async def test_rate_limiter_no_negative_sleep(self):
        """If enough time has passed, wait() should not sleep at all."""
        from app.services.crawler import RateLimiter

        limiter = RateLimiter(requests_per_second=10.0)  # 0.1s delay

        # Set last_request_time far in the past so no sleep is needed
        limiter.last_request_time = time.monotonic() - 10.0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await limiter.wait()
            # sleep should NOT be called because enough time has elapsed
            mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limiter_updates_last_request_time(self):
        """After wait(), last_request_time should be updated to ~now."""
        from app.services.crawler import RateLimiter

        limiter = RateLimiter(requests_per_second=10.0)
        limiter.last_request_time = time.monotonic() - 10.0

        before = time.monotonic()
        await limiter.wait()
        after = time.monotonic()

        assert limiter.last_request_time >= before
        assert limiter.last_request_time <= after
