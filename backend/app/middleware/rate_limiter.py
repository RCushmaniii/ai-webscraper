"""
Rate Limiting Middleware

Implements request rate limiting based on subscription tiers.
Uses Upstash Redis for distributed rate limiting (production) or in-memory for
development. The middleware targets authenticated, mutating endpoints (the
expensive write operations: crawl creation and AI analysis) and identifies the
caller from the JWT `sub` claim, falling back to client IP. Read traffic, health
checks, and static assets are never throttled so normal SPA navigation is
unaffected and we avoid a remote round-trip on every request.
"""

import time
import logging
from typing import Optional, Dict, Tuple
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import jwt

from app.core.config import settings
from app.core.rate_limits import (
    SubscriptionTier,
    get_rate_limit,
    get_tier_from_user,
    get_upgrade_message,
)

logger = logging.getLogger(__name__)

# HTTP methods that mutate state / trigger expensive work. GETs are intentionally
# excluded — a dashboard page view fires several reads and must not hit limits.
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


# ============================================================================
# IN-MEMORY RATE LIMITER (Development/Simple Deployments)
# ============================================================================

class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter for development.

    WARNING: This is NOT suitable for production with multiple workers!
    Use Redis-based limiter for production.
    """

    def __init__(self):
        self.storage: Dict[str, Dict[str, any]] = {}
        self.cleanup_interval = 3600  # Clean up every hour
        self.last_cleanup = time.time()

    def _cleanup_old_entries(self):
        """Remove expired entries from storage."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            to_delete = []
            for key, data in self.storage.items():
                if current_time > data.get("reset_time", 0):
                    to_delete.append(key)

            for key in to_delete:
                del self.storage[key]

            self.last_cleanup = current_time
            logger.debug(f"Cleaned up {len(to_delete)} expired rate limit entries")

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., "user:123:rpm")
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, current_count, reset_time)
        """
        self._cleanup_old_entries()

        current_time = time.time()
        reset_time = current_time + window_seconds

        if key not in self.storage:
            # First request
            self.storage[key] = {
                "count": 1,
                "reset_time": reset_time
            }
            return (True, 1, int(reset_time))

        data = self.storage[key]

        # Check if window has expired
        if current_time > data["reset_time"]:
            # Reset counter
            self.storage[key] = {
                "count": 1,
                "reset_time": reset_time
            }
            return (True, 1, int(reset_time))

        # Increment counter
        data["count"] += 1

        if data["count"] > limit:
            return (False, data["count"], int(data["reset_time"]))

        return (True, data["count"], int(data["reset_time"]))


# Global rate limiter instance
_rate_limiter = InMemoryRateLimiter()


# ============================================================================
# UPSTASH REDIS RATE LIMITER (Production)
# ============================================================================

class UpstashRateLimiter:
    """
    Distributed rate limiter backed by Upstash Redis (REST API).

    Uses a fixed-window counter: INCR the key on every request and set an
    EXPIRE equal to the window on the first hit. The key self-cleans when the
    window elapses, so there is no separate cleanup job. Works across multiple
    workers/instances and survives process restarts (unlike the in-memory
    limiter), which is the whole point of using it in production.
    """

    def __init__(self, url: str, token: str):
        # Imported lazily so the dependency is only required when configured.
        from upstash_redis.asyncio import Redis

        self._redis = Redis(url=url, token=token)

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Atomically increment the window counter and report status.

        Returns:
            Tuple of (allowed, current_count, reset_epoch_seconds).

        Raises:
            Exception: Any transport/Upstash error is propagated so the caller
            can decide how to degrade. We fail OPEN at the call site — a broken
            limiter must never take the API down.
        """
        count = await self._redis.incr(key)

        # Only the first request in a window needs to arm the TTL. Anchoring the
        # window to the first hit keeps this to one round-trip on every
        # subsequent request.
        if count == 1:
            await self._redis.expire(key, window_seconds)

        reset_time = int(time.time()) + window_seconds
        return (count <= limit, count, reset_time)


# Limiter selection: Upstash when configured, in-memory otherwise (dev only).
_upstash_limiter: Optional[UpstashRateLimiter] = None

if settings.RATE_LIMIT_ENABLED:
    try:
        _upstash_limiter = UpstashRateLimiter(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN,
        )
        logger.info("Rate limiting: Upstash Redis limiter active (distributed).")
    except Exception as e:  # pragma: no cover - import/config failure
        logger.error(f"Failed to initialize Upstash limiter, falling back to in-memory: {e}")
        _upstash_limiter = None
else:
    logger.info(
        "Rate limiting: Upstash not configured (UPSTASH_REDIS_REST_URL/TOKEN unset). "
        "Using in-memory limiter — NOT suitable for multi-instance production."
    )


async def _enforce(identity: str, tier: str) -> Tuple[bool, Optional[str], Dict[str, str]]:
    """
    Check per-minute AND per-hour limits for an identity (user id or IP).

    Fails OPEN on any limiter error so an Upstash outage degrades to "allow"
    rather than locking every caller out. Returns (allowed, message, headers).
    """
    limits = get_rate_limit(tier)
    windows = (
        ("rpm", limits.requests_per_minute, 60),
        ("rph", limits.requests_per_hour, 3600),
    )

    for limit_type, limit, window in windows:
        key = f"rl:{identity}:{limit_type}"
        try:
            if _upstash_limiter is not None:
                allowed, current, reset_time = await _upstash_limiter.check_rate_limit(key, limit, window)
            else:
                allowed, current, reset_time = _rate_limiter.check_rate_limit(key, limit, window)
        except Exception as e:
            # Fail open — never block legitimate traffic because the limiter is down.
            logger.warning(f"Rate limiter unavailable ({e}); allowing request for {identity}.")
            return (True, None, {})

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {identity} ({tier}): {current}/{limit} {limit_type}."
            )
            headers = {
                "Retry-After": str(window),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
            }
            return (False, get_upgrade_message(tier, limit_type), headers)

    return (True, None, {})


def _identity_from_request(request: Request) -> Tuple[str, Optional[str]]:
    """
    Derive a rate-limit identity from the request.

    Prefers the authenticated user (JWT `sub`) so limits are per-account. The
    claim is read UNVERIFIED here purely as a bucketing key — forged tokens are
    rejected downstream by get_current_user with a 401, and the IP fallback
    still bounds anonymous/garbage-token floods. Returns (identity, user_id).
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        try:
            sub = jwt.get_unverified_claims(token).get("sub")
            if sub:
                return (f"user:{sub}", sub)
        except Exception:
            pass  # Malformed token — fall through to IP-based bucketing.

    # Behind Caddy the real client IP is the first entry of X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for", "")
    client_ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    return (f"ip:{client_ip}", None)


# ============================================================================
# RATE LIMITING FUNCTIONS
# ============================================================================

def check_rate_limit_for_user(
    user_id: str,
    tier: str,
    limit_type: str = "rpm"  # rpm, rph, rpd
) -> Tuple[bool, Optional[str]]:
    """
    Check rate limit for a user.

    Args:
        user_id: User UUID
        tier: Subscription tier (free, pro, enterprise)
        limit_type: Type of rate limit (rpm, rph, rpd)

    Returns:
        Tuple of (allowed, error_message)
    """
    limits = get_rate_limit(tier)

    # Determine limit and window based on type
    if limit_type == "rpm":
        limit = limits.requests_per_minute
        window = 60  # 1 minute
    elif limit_type == "rph":
        limit = limits.requests_per_hour
        window = 3600  # 1 hour
    elif limit_type == "rpd":
        limit = limits.requests_per_day
        window = 86400  # 1 day
    else:
        logger.error(f"Unknown limit type: {limit_type}")
        return (True, None)  # Allow by default if unknown

    # Check rate limit
    key = f"user:{user_id}:{limit_type}"
    allowed, current, reset_time = _rate_limiter.check_rate_limit(key, limit, window)

    if not allowed:
        error_msg = get_upgrade_message(tier, limit_type)
        logger.warning(
            f"Rate limit exceeded for user {user_id} ({tier}): "
            f"{current}/{limit} {limit_type} (resets at {reset_time})"
        )
        return (False, error_msg)

    logger.debug(f"Rate limit OK for user {user_id}: {current}/{limit} {limit_type}")
    return (True, None)


# ============================================================================
# FASTAPI MIDDLEWARE
# ============================================================================

async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting.

    Only mutating API requests (POST/PUT/PATCH/DELETE under /api/v1) are
    throttled — these are the expensive operations (crawl creation, AI analysis)
    that need protection from abuse. Reads, preflight, health checks, and static
    assets pass straight through, so normal browsing never trips a limit and we
    avoid a remote round-trip on every page load.
    """
    # Fast path: skip anything that isn't a mutating API call.
    if (
        request.method not in _MUTATING_METHODS
        or not request.url.path.startswith(settings.API_V1_STR)
    ):
        return await call_next(request)

    identity, user_id = _identity_from_request(request)

    # Expose the user id to downstream handlers / logging (previously never set,
    # which is why the limiter was inert).
    request.state.user_id = user_id

    tier = get_tier_from_user(user_id) if user_id else SubscriptionTier.FREE.value
    allowed, error_msg, headers = await _enforce(identity, tier)

    if not allowed:
        headers = {**headers, "X-RateLimit-Remaining": "0"}
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": error_msg,
                "retry_after": int(headers.get("Retry-After", "60")),
                "upgrade_url": "/pricing",
            },
            headers=headers,
        )

    return await call_next(request)


# ============================================================================
# DECORATOR FOR ROUTE-SPECIFIC RATE LIMITING
# ============================================================================

def rate_limit(limit_type: str = "rpm"):
    """
    Decorator to apply rate limiting to specific routes.

    Usage:
        @router.post("/crawls")
        @rate_limit("rph")  # Check hourly limit
        async def create_crawl(...):
            ...

    Args:
        limit_type: Type of rate limit (rpm, rph, rpd)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request = kwargs.get("request")
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request:
                user_id = getattr(request.state, "user_id", None)
                if user_id:
                    tier = get_tier_from_user(user_id)
                    allowed, error_msg = check_rate_limit_for_user(user_id, tier, limit_type)

                    if not allowed:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=error_msg
                        )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# USAGE TRACKING (for monthly/crawl limits)
# ============================================================================

def check_monthly_crawl_limit(user_id: str, tier: str) -> Tuple[bool, str]:
    """
    Check if user has exceeded monthly crawl limit.

    Args:
        user_id: User UUID
        tier: Subscription tier

    Returns:
        Tuple of (allowed, error_message)

    TODO: Implement database query when usage tracking table is added
    """
    limits = get_rate_limit(tier)
    monthly_limit = limits.crawls_per_month

    # TODO: Query database for current month's crawl count
    # For now, always allow (will be implemented with usage tracking)
    current_count = 0

    if current_count >= monthly_limit:
        error_msg = get_upgrade_message(tier, "crawls_per_month")
        return (False, error_msg)

    return (True, "")


def check_concurrent_crawls(user_id: str, tier: str) -> Tuple[bool, str]:
    """
    Check if user has exceeded concurrent crawl limit.

    Args:
        user_id: User UUID
        tier: Subscription tier

    Returns:
        Tuple of (allowed, error_message)

    TODO: Implement database query when usage tracking is added
    """
    limits = get_rate_limit(tier)
    concurrent_limit = limits.concurrent_crawls

    # TODO: Query database for active crawls
    # For now, always allow (will be implemented with usage tracking)
    active_crawls = 0

    if active_crawls >= concurrent_limit:
        error_msg = get_upgrade_message(tier, "concurrent_crawls")
        return (False, error_msg)

    return (True, "")


def track_crawl_usage(user_id: str, pages_crawled: int):
    """
    Track crawl usage for billing and analytics.

    Args:
        user_id: User UUID
        pages_crawled: Number of pages crawled

    TODO: Implement when usage tracking table is added
    """
    # TODO: Insert into usage_tracking table
    # For now, just log
    logger.info(f"User {user_id} crawled {pages_crawled} pages")
    pass


# ============================================================================
# ADMIN FUNCTIONS
# ============================================================================

def reset_user_rate_limits(user_id: str):
    """
    Reset all rate limits for a user (admin function).

    Args:
        user_id: User UUID
    """
    # Clear all rate limit keys for this user
    for limit_type in ["rpm", "rph", "rpd"]:
        key = f"user:{user_id}:{limit_type}"
        if key in _rate_limiter.storage:
            del _rate_limiter.storage[key]

    logger.info(f"Reset rate limits for user {user_id}")


def get_user_rate_limit_status(user_id: str, tier: str) -> Dict[str, any]:
    """
    Get current rate limit status for a user.

    Args:
        user_id: User UUID
        tier: Subscription tier

    Returns:
        Dictionary with current status
    """
    limits = get_rate_limit(tier)

    status = {
        "tier": tier,
        "limits": {
            "requests_per_minute": {
                "limit": limits.requests_per_minute,
                "current": _rate_limiter.storage.get(f"user:{user_id}:rpm", {}).get("count", 0),
            },
            "requests_per_hour": {
                "limit": limits.requests_per_hour,
                "current": _rate_limiter.storage.get(f"user:{user_id}:rph", {}).get("count", 0),
            },
            "requests_per_day": {
                "limit": limits.requests_per_day,
                "current": _rate_limiter.storage.get(f"user:{user_id}:rpd", {}).get("count", 0),
            },
        }
    }

    return status
