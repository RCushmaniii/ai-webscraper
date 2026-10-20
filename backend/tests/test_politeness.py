"""
Politeness contract: the behaviours that keep the crawler's single outbound IP
off block lists (app.services.politeness + the crawler's use of it).

- honest bot identity; browser-impersonating agents refused
- robots.txt Disallow / Crawl-delay / Sitemap honoured
- 429 / 503 / CDN challenge -> back off, retry, then stop the crawl
- broken-link probes: one per unique URL, capped per crawl
- one throttle bucket per host, shared across crawls
"""

import time
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services import politeness
from app.services.politeness import (
    BOT_USER_AGENT,
    MAX_CONSECUTIVE_BLOCKS,
    RateLimiter,
    RobotsPolicy,
    backoff_seconds,
    detect_block,
    host_buckets,
    is_browser_impersonating,
    resolve_user_agent,
    retry_after_seconds,
)
from app.services.crawler import MAX_LINK_CHECKS_PER_CRAWL

HTML = "<html><head><title>Hi</title></head><body><h1>Hi</h1><p>hello world</p></body></html>"


def response(status: int, url: str = "https://example.com/", headers=None, text: str = "", content_type: str = "text/html; charset=utf-8"):
    hdrs = {"content-type": content_type}
    hdrs.update(headers or {})
    return httpx.Response(status, headers=hdrs, text=text, request=httpx.Request("GET", url))


@pytest.fixture(autouse=True)
def fresh_host_buckets():
    host_buckets.reset()
    yield
    host_buckets.reset()


@pytest.fixture
def no_sleep():
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        yield mock_sleep


def quiet_crawler(make_crawler, **overrides):
    """A Crawler whose persistence and side-channel calls are mocked, with a mock httpx client."""
    crawler = make_crawler(**overrides)
    crawler.client = MagicMock()
    # The crawler fetches pages with build_request + send(stream=True) so it
    # can time headers separately from the body (2026-10-20). Route that
    # through client.get so tests keep scripting responses on `get` and
    # asserting on its calls.
    crawler.client.build_request = lambda method, url, **kw: httpx.Request(method, url)

    async def _send(request, stream=False, **kw):
        return await crawler.client.get(str(request.url))

    crawler.client.send = AsyncMock(side_effect=_send)
    crawler.client.aclose = AsyncMock()
    crawler._verify_crawl_exists = AsyncMock(return_value=True)
    crawler._save_page_to_db = AsyncMock()
    crawler._save_audit_data = AsyncMock()
    crawler._extract_and_process_links = AsyncMock()
    crawler._extract_and_save_images = AsyncMock(return_value=0)
    crawler._apply_small_site_mode = AsyncMock()
    crawler._save_link = AsyncMock()
    return crawler


# ---------------------------------------------------------------------------
# User agent
# ---------------------------------------------------------------------------

class TestUserAgent:
    def test_default_is_named_bot_with_info_url(self):
        assert resolve_user_agent(None) == BOT_USER_AGENT
        assert resolve_user_agent("   ") == BOT_USER_AGENT
        assert BOT_USER_AGENT.startswith("CushLabsBot/")
        assert "https://scraper.cushlabs.ai/bot.html" in BOT_USER_AGENT

    @pytest.mark.parametrize("ua", [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "chrome/120",
        "Something Safari/605.1.15",
    ])
    def test_browser_strings_are_refused(self, ua):
        assert is_browser_impersonating(ua)
        with pytest.raises(ValueError, match="identify a bot"):
            resolve_user_agent(ua)

    def test_honest_custom_bot_is_accepted(self):
        assert resolve_user_agent("AcmeAuditBot/2.0 (+https://acme.example/bot)") == "AcmeAuditBot/2.0 (+https://acme.example/bot)"

    def test_overlong_agent_is_refused(self):
        with pytest.raises(ValueError, match="characters"):
            resolve_user_agent("Bot/" + "x" * 300)

    def test_crawler_falls_back_to_bot_identity_for_browser_ua(self, make_crawler):
        crawler = make_crawler(user_agent="Mozilla/5.0 Chrome/1.0")
        assert crawler.client.headers["user-agent"] == BOT_USER_AGENT

    def test_crawler_sends_default_identity(self, make_crawler):
        crawler = make_crawler(user_agent=None)
        assert crawler.client.headers["user-agent"] == BOT_USER_AGENT


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------

ROBOTS = """
User-agent: *
Disallow: /private/
Crawl-delay: 4
Sitemap: https://example.com/sitemap.xml

User-agent: CushLabsBot
Disallow: /private/
Disallow: /admin
Crawl-delay: 2
"""


class TestRobotsPolicy:
    def test_disallow_matches_our_token(self):
        policy = RobotsPolicy(BOT_USER_AGENT)
        policy.load_from_text("example.com", ROBOTS)
        assert policy.is_allowed("https://example.com/") is True
        assert policy.is_allowed("https://example.com/blog/post") is True
        assert policy.is_allowed("https://example.com/private/secret") is False
        assert policy.is_allowed("https://example.com/admin") is False

    def test_crawl_delay_and_sitemaps_read_for_our_token(self):
        policy = RobotsPolicy(BOT_USER_AGENT)
        policy.load_from_text("example.com", ROBOTS)
        assert policy.crawl_delay("example.com") == 2.0
        assert policy.sitemaps("example.com") == ["https://example.com/sitemap.xml"]

    def test_wildcard_group_applies_when_no_specific_group(self):
        policy = RobotsPolicy(BOT_USER_AGENT)
        policy.load_from_text("example.com", "User-agent: *\nDisallow: /x\nCrawl-delay: 4\n")
        assert policy.is_allowed("https://example.com/x/y") is False
        assert policy.crawl_delay("example.com") == 4.0

    def test_disabled_policy_allows_everything(self):
        policy = RobotsPolicy(BOT_USER_AGENT, enabled=False)
        policy.load_from_text("example.com", "User-agent: *\nDisallow: /\n")
        assert policy.is_allowed("https://example.com/anything") is True
        assert policy.crawl_delay("example.com") is None

    def test_unloaded_host_fails_open(self):
        policy = RobotsPolicy(BOT_USER_AGENT)
        assert policy.is_allowed("https://never-loaded.example/") is True

    async def test_ensure_loaded_fetches_once_per_host(self):
        policy = RobotsPolicy(BOT_USER_AGENT)
        client = MagicMock()
        client.get = AsyncMock(return_value=response(200, "https://example.com/robots.txt", text="User-agent: *\nDisallow: /nope\n", content_type="text/plain"))
        limiter = RateLimiter(10.0)
        await policy.ensure_loaded(client, "https://example.com/a", limiter)
        await policy.ensure_loaded(client, "https://example.com/b", limiter)
        assert client.get.await_count == 1
        assert client.get.await_args.args[0] == "https://example.com/robots.txt"
        assert policy.is_allowed("https://example.com/nope") is False

    @pytest.mark.parametrize("status", [404, 403, 500])
    async def test_missing_or_broken_robots_means_no_rules(self, status):
        policy = RobotsPolicy(BOT_USER_AGENT)
        client = MagicMock()
        client.get = AsyncMock(return_value=response(status, "https://example.com/robots.txt", text="x"))
        await policy.ensure_loaded(client, "https://example.com/", RateLimiter(10.0))
        assert policy.is_loaded("example.com")
        assert policy.is_allowed("https://example.com/anything") is True

    async def test_fetch_error_means_no_rules(self):
        policy = RobotsPolicy(BOT_USER_AGENT)
        client = MagicMock()
        client.get = AsyncMock(side_effect=httpx.ConnectError("boom"))
        await policy.ensure_loaded(client, "https://example.com/", RateLimiter(10.0))
        assert policy.is_allowed("https://example.com/anything") is True


class TestCrawlerHonoursRobots:
    async def test_disallowed_urls_are_never_fetched(self, make_crawler, no_sleep):
        crawler = quiet_crawler(make_crawler, url="https://example.com/")
        crawler.robots.load_from_text("example.com", ROBOTS)
        crawler._crawl_url = AsyncMock(return_value=None)
        crawler.url_queue = [
            ("https://example.com/private/secret", 0, None, 0, False),
            ("https://example.com/admin", 1, None, 0, False),
            ("https://example.com/ok", 1, None, 0, False),
        ]
        await crawler._crawl()
        fetched = [call.args[0] for call in crawler._crawl_url.await_args_list]
        assert fetched == ["https://example.com/ok"]
        assert crawler.skipped_by_robots == 2

    async def test_start_applies_crawl_delay_before_first_fetch(self, make_crawler, no_sleep):
        crawler = quiet_crawler(make_crawler, url="https://example.com/", rate_limit=2.0)
        crawler.client.get = AsyncMock(return_value=response(200, "https://example.com/robots.txt", text=ROBOTS, content_type="text/plain"))
        crawler._detect_navigation_from_homepage = AsyncMock()
        crawler._crawl = AsyncMock()
        crawler._process_sitemap = AsyncMock()
        await crawler.start()
        # robots said Crawl-delay: 2 for CushLabsBot; the user asked for 2 req/s (0.5s). Robots wins.
        assert crawler.rate_limiter.delay == 2.0
        crawler._process_sitemap.assert_awaited_once_with("https://example.com/sitemap.xml")

    async def test_robots_off_skips_fetch_and_allows_all(self, make_crawler, no_sleep):
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        crawler.client.get = AsyncMock()
        crawler._detect_navigation_from_homepage = AsyncMock()
        crawler._crawl = AsyncMock()
        await crawler.start()
        crawler.client.get.assert_not_awaited()
        assert crawler.robots.is_allowed("https://example.com/private/x") is True


# ---------------------------------------------------------------------------
# Block detection and backoff
# ---------------------------------------------------------------------------

class TestDetectBlock:
    def test_429_is_a_block(self):
        assert "429" in detect_block(429, {}, "")

    def test_503_is_a_block(self):
        assert "503" in detect_block(503, {}, "<html>maintenance</html>")

    def test_403_with_cloudflare_challenge_is_a_block(self):
        body = "<html><head><title>Just a moment...</title></head><body><div id='cf-chl-widget'></div></body></html>"
        assert "challenge" in detect_block(403, {"server": "cloudflare"}, body)

    def test_403_with_cf_mitigated_header_is_a_block(self):
        assert detect_block(403, {"CF-Mitigated": "challenge"}, "") is not None

    def test_plain_403_is_not_a_block(self):
        assert detect_block(403, {"server": "nginx"}, "<html>Forbidden</html>") is None

    @pytest.mark.parametrize("status", [200, 301, 404, 500])
    def test_ordinary_statuses_are_not_blocks(self, status):
        assert detect_block(status, {}, "") is None


class TestRetryAfter:
    def test_delta_seconds(self):
        assert retry_after_seconds({"Retry-After": "30"}) == 30.0

    def test_http_date(self):
        when = datetime.now(timezone.utc) + timedelta(seconds=45)
        got = retry_after_seconds({"retry-after": format_datetime(when, usegmt=True)})
        assert 40 <= got <= 46

    def test_capped(self):
        assert retry_after_seconds({"Retry-After": "99999"}) == politeness.MAX_RETRY_AFTER_SECONDS

    def test_absent_or_garbage(self):
        assert retry_after_seconds({}) is None
        assert retry_after_seconds({"Retry-After": "soon"}) is None

    def test_backoff_prefers_header_then_doubles(self):
        assert backoff_seconds({"Retry-After": "7"}, 1) == 7.0
        assert backoff_seconds({}, 1) == politeness.DEFAULT_BACKOFF_SECONDS
        assert backoff_seconds({}, 2) == politeness.DEFAULT_BACKOFF_SECONDS * 2
        assert backoff_seconds({}, 3) == politeness.DEFAULT_BACKOFF_SECONDS * 4
        assert backoff_seconds({}, 50) == politeness.MAX_RETRY_AFTER_SECONDS


class TestCrawlerBacksOff:
    async def test_persistent_429_retries_then_stops_crawl(self, make_crawler, no_sleep):
        url = "https://example.com/page"
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        crawler.client.get = AsyncMock(return_value=response(429, url, headers={"Retry-After": "7"}, text="slow down"))
        crawler.url_queue = [(url, 0, None, 10, True), ("https://example.com/next", 1, None, 0, False)]

        before = time.monotonic()
        await crawler._crawl()

        # Initial attempt + MAX_RETRIES_PER_URL retries, then the crawl stops:
        # /next is never requested.
        assert crawler.client.get.await_count == MAX_CONSECUTIVE_BLOCKS
        assert all(call.args[0] == url for call in crawler.client.get.await_args_list)
        assert crawler.blocked_reason and "429" in crawler.blocked_reason
        assert crawler.pages_crawled == 0
        crawler._save_page_to_db.assert_not_awaited()
        # Retry-After went onto the HOST bucket, so any other crawl of
        # example.com in this process waits too.
        assert host_buckets.get("example.com").not_before >= before + 7

    async def test_one_429_then_200_recovers(self, make_crawler, no_sleep):
        url = "https://example.com/page"
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        crawler.client.get = AsyncMock(side_effect=[
            response(429, url, text="slow down"),
            response(200, url, text=HTML),
        ])
        crawler.url_queue = [(url, 0, None, 10, True)]
        await crawler._crawl()
        assert crawler.client.get.await_count == 2
        assert crawler.pages_crawled == 1
        assert crawler.consecutive_blocks == 0
        assert crawler.blocked_reason is None
        crawler._save_page_to_db.assert_awaited_once()

    async def test_cloudflare_challenge_page_is_not_saved_as_a_page(self, make_crawler, no_sleep):
        url = "https://example.com/page"
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        challenge = "<html><title>Just a moment...</title><script src='/cdn-cgi/challenge-platform/x.js'></script></html>"
        crawler.client.get = AsyncMock(return_value=response(403, url, headers={"server": "cloudflare"}, text=challenge))
        crawler.url_queue = [(url, 0, None, 10, True)]
        await crawler._crawl()
        crawler._save_page_to_db.assert_not_awaited()
        assert crawler.blocked_reason and "challenge" in crawler.blocked_reason

    async def test_plain_403_is_recorded_as_a_page(self, make_crawler, no_sleep):
        url = "https://example.com/members"
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        crawler.client.get = AsyncMock(return_value=response(403, url, headers={"server": "nginx"}, text="<html>Forbidden</html>"))
        crawler.url_queue = [(url, 0, None, 10, True)]
        await crawler._crawl()
        assert crawler.client.get.await_count == 1
        crawler._save_page_to_db.assert_awaited_once()
        assert crawler.blocked_reason is None


# ---------------------------------------------------------------------------
# Link probes
# ---------------------------------------------------------------------------

def link(url: str) -> dict:
    return {"id": url, "target_url": url, "is_internal": True, "status_code": None, "latency_ms": None, "error": None}


class TestLinkProbes:
    async def test_same_url_probed_once_per_crawl(self, make_crawler, no_sleep):
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        crawler.client.head = AsyncMock(return_value=response(200, "https://example.com/footer"))
        await crawler._check_and_save_link(link("https://example.com/footer"))
        await crawler._check_and_save_link(link("https://example.com/footer"))
        await crawler._check_and_save_link(link("https://example.com/footer/"))  # normalises to the same URL
        assert crawler.client.head.await_count == 1
        assert crawler._save_link.await_count == 3
        assert all(call.args[0]["status_code"] == 200 for call in crawler._save_link.await_args_list)

    async def test_cap_stops_probing_but_still_saves_links(self, make_crawler, no_sleep):
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        crawler.client.head = AsyncMock(return_value=response(200))
        crawler.link_checks_done = MAX_LINK_CHECKS_PER_CRAWL
        await crawler._check_and_save_link(link("https://example.com/one-more"))
        crawler.client.head.assert_not_awaited()
        saved = crawler._save_link.await_args.args[0]
        assert saved["status_code"] is None and saved["is_broken"] is False

    async def test_robots_disallowed_link_is_not_probed(self, make_crawler, no_sleep):
        crawler = quiet_crawler(make_crawler, url="https://example.com/")
        crawler.robots.load_from_text("example.com", ROBOTS)
        crawler.client.head = AsyncMock(return_value=response(200))
        await crawler._check_and_save_link(link("https://example.com/private/doc"))
        crawler.client.head.assert_not_awaited()
        crawler._save_link.assert_awaited_once()

    async def test_probe_429_penalises_host(self, make_crawler, no_sleep):
        crawler = quiet_crawler(make_crawler, url="https://example.com/", respect_robots_txt=False)
        crawler.client.head = AsyncMock(return_value=response(429, headers={"Retry-After": "9"}))
        before = time.monotonic()
        await crawler._check_and_save_link(link("https://example.com/a"))
        assert crawler.consecutive_blocks == 1
        assert host_buckets.get("example.com").not_before >= before + 9


# ---------------------------------------------------------------------------
# Shared per-host throttle
# ---------------------------------------------------------------------------

class TestHostThrottle:
    async def test_two_crawls_of_one_host_share_pacing(self, no_sleep):
        a = RateLimiter(2.0, host="example.com")
        b = RateLimiter(2.0, host="example.com")
        a.last_request_time = time.monotonic()
        await b.wait()
        no_sleep.assert_awaited_once()
        assert 0 < no_sleep.await_args.args[0] <= 0.5

    async def test_different_hosts_do_not_block_each_other(self, no_sleep):
        a = RateLimiter(2.0, host="example.com")
        b = RateLimiter(2.0, host="other.example")
        a.last_request_time = time.monotonic()
        await b.wait()
        no_sleep.assert_not_awaited()

    async def test_penalty_delays_next_request(self, no_sleep):
        limiter = RateLimiter(10.0, host="example.com")
        limiter.last_request_time = time.monotonic() - 100
        limiter.penalize(30)
        await limiter.wait()
        assert no_sleep.await_args.args[0] == pytest.approx(30, abs=0.5)

    def test_crawl_delay_floor_is_capped(self):
        limiter = RateLimiter(2.0)
        limiter.raise_floor(600)
        assert limiter.delay == politeness.MAX_CRAWL_DELAY_SECONDS
        limiter.raise_floor(0.1)  # never lowers
        assert limiter.delay == politeness.MAX_CRAWL_DELAY_SECONDS

    def test_zero_rate_does_not_divide_by_zero(self):
        assert RateLimiter(0).delay == 1.0


# ---------------------------------------------------------------------------
# API: what the crawl-creation route enforces
# ---------------------------------------------------------------------------

@pytest.fixture
def api(request):
    """TestClient with an authenticated user and the Supabase chain mocked.

    ``request.param`` is the ``is_admin`` flag. The inserted crawl row is
    captured in ``client.inserted`` so tests can assert what was persisted.
    """
    from datetime import datetime
    from uuid import uuid4

    from fastapi.testclient import TestClient

    from app.core.auth import get_current_user
    from app.main import app
    from app.models.models import User
    from app.api.routes import crawls as crawls_route

    is_admin = getattr(request, "param", False)
    user = User(id=uuid4(), email="person@example.com", is_admin=is_admin, created_at=datetime.now(), updated_at=datetime.now())

    result = MagicMock()
    result.error = None
    result.count = 1
    result.data = None
    chain = MagicMock()
    for name in ("select", "eq", "single", "delete", "order", "limit"):
        getattr(chain, name).return_value = chain
    chain.execute.return_value = result

    captured = {}

    def insert(data, **kwargs):
        captured.update(data)
        result.data = dict(data)
        return chain

    chain.insert.side_effect = insert
    auth_client = MagicMock()
    auth_client.table.return_value = chain

    app.dependency_overrides[get_current_user] = lambda: user
    with patch.object(crawls_route, "get_auth_client", return_value=auth_client), \
            patch.object(crawls_route, "crawl_site", new=AsyncMock()), \
            patch.object(crawls_route, "log_audit_event"):
        with TestClient(app, raise_server_exceptions=False) as client:
            client.inserted = captured
            yield client
    app.dependency_overrides.pop(get_current_user, None)


BODY = {"url": "https://example.com", "max_depth": 1, "max_pages": 5, "rate_limit": 1}


class TestCreateCrawlRoute:
    def test_browser_user_agent_is_refused_with_422(self, api):
        r = api.post("/api/v1/crawls/", json={**BODY, "user_agent": "Mozilla/5.0 Chrome/120 Safari/537.36"})
        assert r.status_code == 422, r.text
        assert "identify a bot" in r.json()["detail"]
        assert api.inserted == {}

    def test_empty_user_agent_becomes_bot_identity(self, api):
        r = api.post("/api/v1/crawls/", json={**BODY, "user_agent": ""})
        assert r.status_code == 200, r.text
        assert api.inserted["user_agent"] == BOT_USER_AGENT

    def test_free_user_cannot_switch_robots_off(self, api):
        r = api.post("/api/v1/crawls/", json={**BODY, "respect_robots_txt": False})
        assert r.status_code == 200, r.text
        assert api.inserted["respect_robots_txt"] is True

    def test_fractional_rate_limit_survives(self, api):
        r = api.post("/api/v1/crawls/", json={**BODY, "rate_limit": 0.5})
        assert r.status_code == 200, r.text
        assert api.inserted["rate_limit"] == 0.5

    @pytest.mark.parametrize("api", [True], indirect=True)
    def test_admin_may_switch_robots_off(self, api):
        r = api.post("/api/v1/crawls/", json={**BODY, "respect_robots_txt": False})
        assert r.status_code == 200, r.text
        assert api.inserted["respect_robots_txt"] is False
