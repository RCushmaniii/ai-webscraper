"""
Tests for the domain blacklist module.

Verifies that known-bad domains (social media, analytics, ads, etc.)
are correctly blocked and normal domains are allowed.
"""

import pytest

from app.core.domain_blacklist import (
    is_domain_blacklisted,
    get_blacklist_reason,
    get_blacklist_stats,
)


class TestIsDomainBlacklisted:

    def test_blocks_facebook(self):
        assert is_domain_blacklisted("https://facebook.com/share") is True

    def test_blocks_twitter(self):
        assert is_domain_blacklisted("https://twitter.com/user") is True

    def test_blocks_x_com(self):
        assert is_domain_blacklisted("https://x.com/user") is True

    def test_blocks_instagram(self):
        assert is_domain_blacklisted("https://instagram.com/p/abc123") is True

    def test_blocks_linkedin(self):
        assert is_domain_blacklisted("https://linkedin.com/in/somebody") is True

    def test_blocks_youtube(self):
        assert is_domain_blacklisted("https://youtube.com/watch?v=abc") is True

    def test_blocks_google_analytics(self):
        assert is_domain_blacklisted("https://google-analytics.com/collect") is True

    def test_blocks_doubleclick(self):
        assert is_domain_blacklisted("https://doubleclick.net/ads") is True

    def test_allows_regular_domain(self):
        assert is_domain_blacklisted("https://example.com") is False

    def test_allows_cushlabs_domain(self):
        assert is_domain_blacklisted("https://cushlabs.com") is False

    def test_blocks_subdomain_of_blacklisted(self):
        """m.facebook.com should be blocked because facebook.com is blacklisted."""
        assert is_domain_blacklisted("https://m.facebook.com/page") is True

    def test_blocks_www_prefix(self):
        """www.facebook.com should also be blocked."""
        assert is_domain_blacklisted("https://www.facebook.com") is True

    def test_blocks_ecommerce(self):
        assert is_domain_blacklisted("https://amazon.com/product") is True

    def test_blocks_cdn(self):
        assert is_domain_blacklisted("https://cloudflare.com") is True

    def test_blocks_file_sharing(self):
        assert is_domain_blacklisted("https://drive.google.com/file/d/abc") is True

    def test_empty_netloc_not_blacklisted(self):
        """URLs with no recognizable domain are not in the blacklist."""
        # urlparse doesn't raise on malformed input; it returns empty netloc
        assert is_domain_blacklisted("not-a-url") is False


class TestGetBlacklistReason:

    def test_facebook_reason_is_social_media(self):
        reason = get_blacklist_reason("https://facebook.com/share")
        assert reason == "social_media"

    def test_google_analytics_reason(self):
        reason = get_blacklist_reason("https://google-analytics.com/collect")
        assert reason == "analytics"

    def test_regular_domain_empty_reason(self):
        reason = get_blacklist_reason("https://example.com")
        assert reason == ""


class TestGetBlacklistStats:

    def test_stats_has_all_categories(self):
        stats = get_blacklist_stats()
        assert "total_domains" in stats
        assert "social_media" in stats
        assert "analytics" in stats
        assert "ads" in stats
        assert stats["total_domains"] > 0

    def test_total_is_sum_of_categories(self):
        stats = get_blacklist_stats()
        category_sum = (
            stats["social_media"]
            + stats["analytics"]
            + stats["ads"]
            + stats["cdn"]
            + stats["auth"]
            + stats["search_engines"]
            + stats["ecommerce"]
            + stats["file_sharing"]
            + stats["adult_content"]
        )
        # Total should equal the union of all sets (may be <= sum if sets overlap)
        assert stats["total_domains"] <= category_sum
        assert stats["total_domains"] > 0
