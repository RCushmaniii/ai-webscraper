"""
Rate Limiting Middleware

Implements request rate limiting based on subscription tiers.
Uses Redis for distributed rate limiting (production) or in-memory for development.
"""

import time
import logging
from typing import Optional, Dict, Tuple
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.rate_limits import get_rate_limit, get_tier_from_user, get_upgrade_message

logger = logging.getLogger(__name__)


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
# REDIS RATE LIMITER (Production)
# ============================================================================

class RedisRateLimiter:
    """
    Redis-based rate limiter for production use.

    Supports distributed rate limiting across multiple workers/servers.

    TODO: Implement when Redis is added to infrastructure
    """

    def __init__(self, redis_url: str):
        """
        Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL
        """
        # TODO: Implement Redis connection
        raise NotImplementedError("Redis rate limiter not yet implemented. Use InMemoryRateLimiter for now.")


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

    Checks rate limits for authenticated users on every request.
    """
    # Skip rate limiting for health checks and static files
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get user from request (if authenticated)
    user_id = getattr(request.state, "user_id", None)

    if user_id:
        # Get user's subscription tier
        tier = get_tier_from_user(user_id)

        # Check rate limit (requests per minute)
        allowed, error_msg = check_rate_limit_for_user(user_id, tier, "rpm")

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": error_msg,
                    "retry_after": 60,  # Retry after 1 minute
                    "upgrade_url": "/pricing"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(get_rate_limit(tier).requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )

    # Continue to next middleware/route
    response = await call_next(request)
    return response


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
