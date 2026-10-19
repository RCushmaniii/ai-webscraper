"""
Politeness layer for the crawler.

Everything that keeps the one outbound IP (the Hetzner box every crawl leaves
from) off block lists lives here, so the crawler itself stays about fetching
and parsing:

- An honest bot identity (``BOT_USER_AGENT``) and a validator that refuses
  browser-impersonating user agents. A request that pretends to be Chrome is
  what turns a polite audit tool into "a scraper" in a site owner's logs.
- ``RobotsPolicy``: robots.txt ``Disallow``, ``Crawl-delay`` and ``Sitemap``
  handling. Before 2026-10-19 the "respect robots.txt" option only read the
  Sitemap lines; Disallow was ignored.
- ``HostBucket`` / ``host_buckets``: one throttle bucket per host, shared by
  every crawl running in this process, so three concurrent crawls of one site
  do not triple the request rate. A bucket also carries a penalty window that
  a 429/503 pushes forward.
- ``detect_block`` / ``retry_after_seconds``: recognise a site pushing back
  (429, 503, CDN bot challenges) so the crawler backs off and eventually stops
  instead of hammering until max_pages.

Nothing here imports from the rest of the app, so config and the crawler can
both import it without cycles.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Mapping, Optional
from urllib import robotparser
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bot identity
# ---------------------------------------------------------------------------

BOT_NAME = "CushLabsBot"
BOT_INFO_URL = "https://scraper.cushlabs.ai/bot.html"
BOT_USER_AGENT = f"{BOT_NAME}/1.0 (+{BOT_INFO_URL})"

# Substrings that only appear in real browser user agents (or in strings
# built to look like one). Case-insensitive.
_BROWSER_UA_MARKERS = (
    "mozilla/",
    "applewebkit",
    "chrome/",
    "chromium/",
    "safari/",
    "firefox/",
    "edg/",
    "edge/",
    "opr/",
    "opera/",
    "gecko/",
    "trident/",
    "msie ",
)

MAX_USER_AGENT_LENGTH = 200


def is_browser_impersonating(user_agent: str) -> bool:
    """True when the string looks like a browser rather than a named bot."""
    ua = (user_agent or "").lower()
    return any(marker in ua for marker in _BROWSER_UA_MARKERS)


def resolve_user_agent(requested: Optional[str]) -> str:
    """Return the user agent a crawl must send.

    Empty -> the CushLabs bot identity. A custom value is accepted only when it
    names a bot (anything that does not look like a browser) and is short
    enough to be sane. Raises ``ValueError`` with a user-facing message
    otherwise; the API turns that into a 422.
    """
    ua = (requested or "").strip()
    if not ua:
        return BOT_USER_AGENT
    if len(ua) > MAX_USER_AGENT_LENGTH:
        raise ValueError(f"User agent must be {MAX_USER_AGENT_LENGTH} characters or fewer")
    if is_browser_impersonating(ua):
        raise ValueError(
            "User agent must identify a bot. Browser user agents (Mozilla/Chrome/Safari/...) "
            f"are not accepted; leave the field empty to use {BOT_USER_AGENT}"
        )
    return ua


def agent_token(user_agent: str) -> str:
    """The product token robots.txt matches on: ``CushLabsBot/1.0 (...)`` -> ``CushLabsBot``."""
    return (user_agent or "").split("/", 1)[0].split(" ", 1)[0].strip() or "*"


# ---------------------------------------------------------------------------
# Per-host throttle shared across crawls
# ---------------------------------------------------------------------------

MAX_CRAWL_DELAY_SECONDS = 30.0  # honour Crawl-delay up to this; beyond it a 50-page crawl never finishes


@dataclass
class HostBucket:
    """Request pacing state for one host. Shared by every crawler in-process."""

    last_request_time: float = 0.0
    not_before: float = 0.0  # monotonic time before which no request may go out (penalty)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def penalize(self, seconds: float) -> None:
        self.not_before = max(self.not_before, time.monotonic() + max(0.0, seconds))


class HostBucketRegistry:
    def __init__(self) -> None:
        self._buckets: Dict[str, HostBucket] = {}

    def get(self, host: str) -> HostBucket:
        key = (host or "").lower()
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = HostBucket()
            self._buckets[key] = bucket
        return bucket

    def reset(self) -> None:
        """Tests only."""
        self._buckets.clear()


host_buckets = HostBucketRegistry()


class RateLimiter:
    """Paces requests for one crawl.

    ``delay`` is the minimum interval between requests (1 / requests_per_second,
    raised by robots.txt Crawl-delay). Pacing state lives in the host's shared
    bucket when ``host`` is given, so concurrent crawls of the same site queue
    behind each other instead of stacking.
    """

    def __init__(self, requests_per_second: float, host: Optional[str] = None):
        rps = float(requests_per_second) if requests_per_second else 0.0
        if rps <= 0:
            rps = 1.0  # the API clamps to >= 0.1; this guards a bad DB row
        self.delay = 1.0 / rps
        self._default_bucket = host_buckets.get(host) if host else HostBucket()

    # Compatibility with code/tests that poke the old single-bucket limiter.
    @property
    def last_request_time(self) -> float:
        return self._default_bucket.last_request_time

    @last_request_time.setter
    def last_request_time(self, value: float) -> None:
        self._default_bucket.last_request_time = value

    def _bucket_for(self, url: Optional[str]) -> HostBucket:
        if not url:
            return self._default_bucket
        return host_buckets.get(urlparse(url).netloc)

    def raise_floor(self, seconds: Optional[float]) -> None:
        """Never go faster than ``seconds`` between requests (robots Crawl-delay)."""
        if seconds is None:
            return
        self.delay = max(self.delay, min(float(seconds), MAX_CRAWL_DELAY_SECONDS))

    def penalize(self, seconds: float, url: Optional[str] = None) -> None:
        self._bucket_for(url).penalize(seconds)

    async def wait(self, url: Optional[str] = None) -> None:
        bucket = self._bucket_for(url)
        async with bucket.lock:
            now = time.monotonic()
            target = max(bucket.last_request_time + self.delay, bucket.not_before)
            sleep_time = target - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            bucket.last_request_time = time.monotonic()


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------


class RobotsPolicy:
    """robots.txt rules per host, matched against our product token.

    ``ensure_loaded`` fetches each host's robots.txt once (through the
    limiter, like any other request). A missing or erroring robots.txt means
    "no rules", the same reading Google applies to 4xx.
    """

    def __init__(self, user_agent: str, enabled: bool = True):
        self.enabled = enabled
        self.token = agent_token(user_agent)
        self._parsers: Dict[str, Optional[robotparser.RobotFileParser]] = {}

    @staticmethod
    def _allow_all_parser() -> robotparser.RobotFileParser:
        rp = robotparser.RobotFileParser()
        rp.allow_all = True
        rp.modified()
        return rp

    def load_from_text(self, host: str, text: str) -> None:
        rp = robotparser.RobotFileParser()
        rp.parse(text.splitlines())
        self._parsers[host.lower()] = rp

    def is_loaded(self, host: str) -> bool:
        return host.lower() in self._parsers

    async def ensure_loaded(self, client, url: str, limiter: RateLimiter) -> None:
        """Fetch and parse robots.txt for ``url``'s host if not seen yet."""
        if not self.enabled:
            return
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if not host or host in self._parsers:
            return
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            await limiter.wait(robots_url)
            response = await client.get(robots_url)
            if response.status_code == 200:
                self.load_from_text(host, response.text)
                rp = self._parsers[host]
                logger.info(
                    f"robots.txt loaded for {host}: crawl-delay={rp.crawl_delay(self.token)} "
                    f"sitemaps={len(rp.site_maps() or [])}"
                )
            else:
                # 4xx (no file) and 5xx (broken server) both read as "no rules";
                # failing the whole crawl over a 500 on robots.txt helps nobody.
                logger.info(f"robots.txt for {host} returned {response.status_code}; treating as no rules")
                self._parsers[host] = self._allow_all_parser()
        except Exception as e:
            logger.warning(f"robots.txt fetch failed for {host}: {e}; treating as no rules")
            self._parsers[host] = self._allow_all_parser()

    def is_allowed(self, url: str) -> bool:
        if not self.enabled:
            return True
        host = urlparse(url).netloc.lower()
        rp = self._parsers.get(host)
        if rp is None:
            return True  # not loaded (e.g. the caller skipped ensure_loaded); fail open
        try:
            return rp.can_fetch(self.token, url)
        except Exception:
            return True

    def crawl_delay(self, host: str) -> Optional[float]:
        rp = self._parsers.get((host or "").lower())
        if rp is None or not self.enabled:
            return None
        try:
            delay = rp.crawl_delay(self.token)
            return float(delay) if delay is not None else None
        except Exception:
            return None

    def sitemaps(self, host: str) -> List[str]:
        rp = self._parsers.get((host or "").lower())
        if rp is None:
            return []
        try:
            return list(rp.site_maps() or [])
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Block detection and backoff
# ---------------------------------------------------------------------------

MAX_CONSECUTIVE_BLOCKS = 3  # stop the crawl after this many blocked responses in a row
MAX_RETRIES_PER_URL = 2  # re-queue a blocked URL at most this many times
MAX_RETRY_AFTER_SECONDS = 120.0
DEFAULT_BACKOFF_SECONDS = 10.0  # first backoff when the site sends no Retry-After; doubles each time

# Markers of CDN / WAF interstitials. Lower-case; matched against headers and
# the first few KB of the body.
_CHALLENGE_BODY_MARKERS = (
    "just a moment...",
    "attention required! | cloudflare",
    "cf-chl",
    "challenge-platform",
    "_incapsula_resource",
    "incapsula incident",
    "perimeterx",
    "px-captcha",
    "datadome",
    "ddos-guard",
    "errors.edgesuite.net",
    "request unsuccessful. incapsula",
    "please verify you are a human",
    "bot verification",
)


def retry_after_seconds(headers: Mapping[str, str]) -> Optional[float]:
    """Parse Retry-After (delta-seconds or HTTP-date), capped. None when absent/invalid."""
    raw = None
    for key, value in headers.items():
        if key.lower() == "retry-after":
            raw = value
            break
    if raw is None:
        return None
    raw = raw.strip()
    seconds: Optional[float] = None
    if raw.isdigit():
        seconds = float(raw)
    else:
        try:
            when = parsedate_to_datetime(raw)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            seconds = (when - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, IndexError):
            return None
    if seconds is None:
        return None
    return max(0.0, min(seconds, MAX_RETRY_AFTER_SECONDS))


def detect_block(status_code: int, headers: Mapping[str, str], body_sample: str = "") -> Optional[str]:
    """Return a short reason when the response means "stop hitting me", else None.

    429 always. 503 always (overloaded or a challenge; either way back off).
    403 only when it carries a CDN challenge, since a plain 403 is just a
    private page.
    """
    if status_code == 429:
        return "rate limited (HTTP 429)"
    lowered_headers = {k.lower(): (v or "").lower() for k, v in headers.items()}
    body = (body_sample or "")[:8192].lower()
    challenge = (
        lowered_headers.get("cf-mitigated") == "challenge"
        or any(marker in body for marker in _CHALLENGE_BODY_MARKERS)
    )
    if status_code == 503:
        return "bot challenge (HTTP 503)" if challenge else "service unavailable (HTTP 503)"
    if status_code == 403 and challenge:
        return "bot challenge (HTTP 403)"
    return None


def backoff_seconds(headers: Mapping[str, str], consecutive_blocks: int) -> float:
    """Retry-After when the site says so, else exponential from DEFAULT_BACKOFF_SECONDS."""
    hinted = retry_after_seconds(headers)
    if hinted is not None:
        return hinted
    exponent = max(0, consecutive_blocks - 1)
    return min(DEFAULT_BACKOFF_SECONDS * (2 ** exponent), MAX_RETRY_AFTER_SECONDS)
