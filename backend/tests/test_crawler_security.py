"""
Tests for SSRF protection in the Crawler.

The crawler must block requests to private/reserved IP ranges to prevent
Server-Side Request Forgery attacks. These tests verify that _is_private_ip
and _should_crawl_url correctly reject dangerous targets.
"""

import socket
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# _is_private_ip tests
# ---------------------------------------------------------------------------

class TestIsPrivateIp:
    """Verify that _is_private_ip blocks reserved/private addresses."""

    def _resolve(self, ip_str):
        """Helper: fake socket.getaddrinfo returning a single IPv4 result."""
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", (ip_str, 0))]

    def test_blocks_localhost(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("127.0.0.1")):
            assert crawler._is_private_ip("localhost") is True

    def test_blocks_private_class_a(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("10.0.0.1")):
            assert crawler._is_private_ip("internal.corp") is True

    def test_blocks_private_class_b(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("172.16.0.1")):
            assert crawler._is_private_ip("internal.corp") is True

    def test_blocks_private_class_c(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("192.168.1.1")):
            assert crawler._is_private_ip("home.local") is True

    def test_blocks_aws_metadata(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("169.254.169.254")):
            assert crawler._is_private_ip("metadata.internal") is True

    def test_blocks_ipv6_loopback(self, make_crawler):
        crawler = make_crawler()
        ipv6_result = [(socket.AF_INET6, socket.SOCK_STREAM, 0, "", ("::1", 0, 0, 0))]
        with patch("socket.getaddrinfo", return_value=ipv6_result):
            assert crawler._is_private_ip("localhost6") is True

    def test_allows_public_ip(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("8.8.8.8")):
            assert crawler._is_private_ip("dns.google") is False

    def test_allows_public_domain(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("93.184.216.34")):
            assert crawler._is_private_ip("example.com") is False

    def test_blocks_zero_network(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", return_value=self._resolve("0.0.0.0")):
            assert crawler._is_private_ip("zero.test") is True

    def test_blocks_on_dns_failure(self, make_crawler):
        """If DNS fails, err on the side of caution and block."""
        crawler = make_crawler()
        with patch("socket.getaddrinfo", side_effect=socket.gaierror("DNS fail")):
            assert crawler._is_private_ip("nonexistent.local") is True


# ---------------------------------------------------------------------------
# _should_crawl_url SSRF-related tests
# ---------------------------------------------------------------------------

class TestShouldCrawlUrlSecurity:
    """Verify _should_crawl_url blocks private IPs even as raw URLs."""

    def _resolve_public(self, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("93.184.216.34", 0))]

    def test_blocks_raw_localhost_ip(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("http://127.0.0.1/admin") is False

    def test_blocks_raw_private_10(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("http://10.0.0.5/secret") is False

    def test_blocks_raw_private_172(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("http://172.16.0.1/") is False

    def test_blocks_raw_private_192(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("http://192.168.0.1/") is False

    def test_blocks_raw_aws_metadata(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("http://169.254.169.254/latest/meta-data/") is False

    def test_blocks_raw_zero_ip(self, make_crawler):
        crawler = make_crawler()
        assert crawler._should_crawl_url("http://0.0.0.0/") is False

    def test_allows_public_url(self, make_crawler):
        crawler = make_crawler()
        with patch("socket.getaddrinfo", side_effect=self._resolve_public):
            assert crawler._should_crawl_url("https://example.com/page") is True
