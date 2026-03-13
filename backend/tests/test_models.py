"""
Tests for Pydantic model validation.

Verifies that CrawlBase, UserBase, and related models enforce their constraints
(URL format, field bounds, email validation, defaults).
"""

import pytest
from pydantic import ValidationError

from app.models.models import CrawlBase, UserBase


# ---------------------------------------------------------------------------
# CrawlBase validation
# ---------------------------------------------------------------------------

class TestCrawlBaseValidation:

    def test_crawl_base_valid(self):
        crawl = CrawlBase(url="https://example.com")
        assert crawl.url == "https://example.com"
        assert crawl.max_depth == 2  # default
        assert crawl.max_pages == 10  # default

    def test_crawl_base_valid_http(self):
        crawl = CrawlBase(url="http://example.com")
        assert crawl.url == "http://example.com"

    def test_crawl_base_url_too_long(self):
        long_url = "https://example.com/" + "a" * 2048
        with pytest.raises(ValidationError) as exc_info:
            CrawlBase(url=long_url)
        # Should fail on max_length=2048
        assert "max_length" in str(exc_info.value).lower() or "string_too_long" in str(exc_info.value).lower()

    def test_crawl_base_url_invalid_scheme_ftp(self):
        with pytest.raises(ValidationError) as exc_info:
            CrawlBase(url="ftp://example.com/file")
        assert "http" in str(exc_info.value).lower()

    def test_crawl_base_url_invalid_scheme_no_scheme(self):
        with pytest.raises(ValidationError) as exc_info:
            CrawlBase(url="example.com")
        assert "http" in str(exc_info.value).lower()

    def test_crawl_base_max_depth_too_high(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", max_depth=11)

    def test_crawl_base_max_depth_too_low(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", max_depth=0)

    def test_crawl_base_max_depth_boundary_valid(self):
        crawl = CrawlBase(url="https://example.com", max_depth=10)
        assert crawl.max_depth == 10

        crawl = CrawlBase(url="https://example.com", max_depth=1)
        assert crawl.max_depth == 1

    def test_crawl_base_max_pages_too_high(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", max_pages=5001)

    def test_crawl_base_max_pages_too_low(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", max_pages=0)

    def test_crawl_base_max_pages_defaults(self):
        crawl = CrawlBase(url="https://example.com")
        assert crawl.max_pages == 10

    def test_crawl_base_rate_limit_defaults(self):
        crawl = CrawlBase(url="https://example.com")
        assert crawl.rate_limit == 2.0

    def test_crawl_base_rate_limit_too_low(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", rate_limit=0.05)

    def test_crawl_base_rate_limit_too_high(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", rate_limit=11.0)

    def test_crawl_base_follow_external_links_default_false(self):
        crawl = CrawlBase(url="https://example.com")
        assert crawl.follow_external_links is False

    def test_crawl_base_js_rendering_default_false(self):
        crawl = CrawlBase(url="https://example.com")
        assert crawl.js_rendering is False

    def test_crawl_base_max_runtime_sec_too_low(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", max_runtime_sec=30)

    def test_crawl_base_max_runtime_sec_too_high(self):
        with pytest.raises(ValidationError):
            CrawlBase(url="https://example.com", max_runtime_sec=90000)


# ---------------------------------------------------------------------------
# UserBase validation
# ---------------------------------------------------------------------------

class TestUserBaseValidation:

    def test_user_base_valid_email(self):
        user = UserBase(email="user@example.com")
        assert user.email == "user@example.com"
        assert user.is_active is True
        assert user.is_admin is False

    def test_user_base_invalid_email(self):
        with pytest.raises(ValidationError):
            UserBase(email="not-an-email")

    def test_user_base_missing_email(self):
        with pytest.raises(ValidationError):
            UserBase()

    def test_user_base_admin_override(self):
        user = UserBase(email="admin@example.com", is_admin=True)
        assert user.is_admin is True
