"""
Rate Limiting Configuration

Defines rate limits for different subscription tiers.
This follows industry best practices:
- Free tier: Limited to prevent abuse
- Pro tier: Generous limits for paying customers
- Enterprise: Unlimited or very high limits
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass


class SubscriptionTier(str, Enum):
    """Subscription tier enumeration."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"  # Internal admin users


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    crawls_per_month: int
    pages_per_crawl: int
    concurrent_crawls: int
    api_requests_per_day: int


# ============================================================================
# RATE LIMIT DEFINITIONS BY TIER
# ============================================================================

RATE_LIMITS: Dict[SubscriptionTier, RateLimit] = {
    # Free Tier - Limited but usable for personal projects
    SubscriptionTier.FREE: RateLimit(
        requests_per_minute=10,          # Prevent rapid-fire requests
        requests_per_hour=100,            # ~1-2 crawls per hour
        requests_per_day=500,             # Reasonable daily usage
        crawls_per_month=5,               # 5 crawls/month (freemium model)
        pages_per_crawl=50,               # Limited crawl depth
        concurrent_crawls=1,              # One at a time
        api_requests_per_day=100,         # Minimal API usage
    ),

    # Pro Tier - $29/month - Generous limits for professionals
    SubscriptionTier.PRO: RateLimit(
        requests_per_minute=60,           # Much higher rate
        requests_per_hour=1000,           # ~10-20 crawls per hour
        requests_per_day=10000,           # Heavy daily usage
        crawls_per_month=100,             # 100 crawls/month
        pages_per_crawl=1000,             # Deep crawls allowed
        concurrent_crawls=3,              # Multiple simultaneous crawls
        api_requests_per_day=1000,        # API access included
    ),

    # Enterprise Tier - Custom pricing - Virtually unlimited
    SubscriptionTier.ENTERPRISE: RateLimit(
        requests_per_minute=300,          # Very high rate
        requests_per_hour=10000,          # Unlimited crawls
        requests_per_day=100000,          # Enterprise-grade usage
        crawls_per_month=999999,          # Effectively unlimited
        pages_per_crawl=10000,            # Large-scale crawls
        concurrent_crawls=10,             # Many simultaneous crawls
        api_requests_per_day=100000,      # Full API access
    ),

    # Admin Tier - Internal use - No limits
    SubscriptionTier.ADMIN: RateLimit(
        requests_per_minute=999999,       # No limit
        requests_per_hour=999999,         # No limit
        requests_per_day=999999,          # No limit
        crawls_per_month=999999,          # No limit
        pages_per_crawl=999999,           # No limit
        concurrent_crawls=999999,         # No limit
        api_requests_per_day=999999,      # No limit
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_rate_limit(tier: str) -> RateLimit:
    """
    Get rate limit configuration for a subscription tier.

    Args:
        tier: Subscription tier name (free, pro, enterprise, admin)

    Returns:
        RateLimit configuration for the tier

    Raises:
        ValueError: If tier is unknown
    """
    try:
        tier_enum = SubscriptionTier(tier.lower())
        return RATE_LIMITS[tier_enum]
    except ValueError:
        # Default to free tier if tier is unknown
        return RATE_LIMITS[SubscriptionTier.FREE]


def get_tier_from_user(user_id: str) -> str:
    """
    Get subscription tier for a user.

    This is a placeholder - in production, this would:
    1. Query the subscriptions table
    2. Check Stripe subscription status
    3. Verify payment status
    4. Return the appropriate tier

    Args:
        user_id: User UUID

    Returns:
        Subscription tier name

    TODO: Implement actual subscription lookup when Stripe is integrated
    """
    # TODO: Replace with actual database query
    # For now, everyone is on free tier
    return SubscriptionTier.FREE.value


def check_monthly_crawl_limit(user_id: str, tier: str) -> tuple[bool, int, int]:
    """
    Check if user has exceeded their monthly crawl limit.

    Args:
        user_id: User UUID
        tier: Subscription tier

    Returns:
        Tuple of (within_limit, current_count, limit)

    TODO: Implement actual database query when usage tracking is added
    """
    limit_config = get_rate_limit(tier)
    monthly_limit = limit_config.crawls_per_month

    # TODO: Query database for actual usage
    # For now, always return within limit
    current_count = 0

    return (current_count < monthly_limit, current_count, monthly_limit)


def check_concurrent_crawl_limit(user_id: str, tier: str) -> tuple[bool, int, int]:
    """
    Check if user has exceeded their concurrent crawl limit.

    Args:
        user_id: User UUID
        tier: Subscription tier

    Returns:
        Tuple of (within_limit, current_count, limit)

    TODO: Implement actual database query when usage tracking is added
    """
    limit_config = get_rate_limit(tier)
    concurrent_limit = limit_config.concurrent_crawls

    # TODO: Query database for active crawls
    # For now, always return within limit
    current_count = 0

    return (current_count < concurrent_limit, current_count, concurrent_limit)


# ============================================================================
# RATE LIMIT MESSAGES
# ============================================================================

RATE_LIMIT_MESSAGES = {
    "rpm": "Rate limit exceeded: Too many requests per minute. Please slow down.",
    "rph": "Rate limit exceeded: Too many requests per hour. Please try again later.",
    "rpd": "Rate limit exceeded: Daily request limit reached. Upgrade to Pro for higher limits.",
    "crawls_per_month": "Monthly crawl limit reached. Upgrade to Pro for 100 crawls/month.",
    "pages_per_crawl": "Page limit exceeded for this crawl. Upgrade to Pro for deeper crawls.",
    "concurrent_crawls": "Concurrent crawl limit reached. Wait for existing crawls to finish or upgrade to Pro.",
    "api_requests": "Daily API request limit reached. Upgrade to Pro for higher API limits.",
}


def get_upgrade_message(tier: str, limit_type: str) -> str:
    """
    Get user-friendly upgrade message for a rate limit.

    Args:
        tier: Current subscription tier
        limit_type: Type of limit hit (rpm, rph, crawls_per_month, etc.)

    Returns:
        User-friendly message with upgrade suggestion
    """
    base_message = RATE_LIMIT_MESSAGES.get(limit_type, "Rate limit exceeded.")

    if tier == SubscriptionTier.FREE.value:
        upgrade_message = " Upgrade to Pro ($29/month) for much higher limits."
        return base_message + upgrade_message
    elif tier == SubscriptionTier.PRO.value:
        upgrade_message = " Contact sales for Enterprise tier with unlimited usage."
        return base_message + upgrade_message
    else:
        return base_message


# ============================================================================
# RATE LIMIT COMPARISON (for pricing page)
# ============================================================================

def get_tier_comparison() -> Dict[str, Dict[str, any]]:
    """
    Get rate limit comparison for all tiers (useful for pricing page).

    Returns:
        Dictionary with tier comparisons
    """
    return {
        "free": {
            "name": "Free",
            "price": "$0",
            "crawls_per_month": RATE_LIMITS[SubscriptionTier.FREE].crawls_per_month,
            "pages_per_crawl": RATE_LIMITS[SubscriptionTier.FREE].pages_per_crawl,
            "concurrent_crawls": RATE_LIMITS[SubscriptionTier.FREE].concurrent_crawls,
            "api_requests_per_day": RATE_LIMITS[SubscriptionTier.FREE].api_requests_per_day,
        },
        "pro": {
            "name": "Pro",
            "price": "$29",
            "crawls_per_month": RATE_LIMITS[SubscriptionTier.PRO].crawls_per_month,
            "pages_per_crawl": RATE_LIMITS[SubscriptionTier.PRO].pages_per_crawl,
            "concurrent_crawls": RATE_LIMITS[SubscriptionTier.PRO].concurrent_crawls,
            "api_requests_per_day": RATE_LIMITS[SubscriptionTier.PRO].api_requests_per_day,
        },
        "enterprise": {
            "name": "Enterprise",
            "price": "Custom",
            "crawls_per_month": "Unlimited",
            "pages_per_crawl": RATE_LIMITS[SubscriptionTier.ENTERPRISE].pages_per_crawl,
            "concurrent_crawls": RATE_LIMITS[SubscriptionTier.ENTERPRISE].concurrent_crawls,
            "api_requests_per_day": RATE_LIMITS[SubscriptionTier.ENTERPRISE].api_requests_per_day,
        },
    }
