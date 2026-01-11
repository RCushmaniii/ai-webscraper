"""
Domain Blacklist Configuration

Domains that should NEVER be crawled to prevent:
- Following links to social media (infinite pages)
- Tracking/analytics sites
- Ad networks
- Login/authentication pages
- Known problematic domains

This is a safety mechanism when follow_external_links is enabled.
"""

from typing import Set
from urllib.parse import urlparse

# ============================================================================
# BLACKLIST CATEGORIES
# ============================================================================

# Social Media (infinite content, rate limits, ToS issues)
SOCIAL_MEDIA_DOMAINS: Set[str] = {
    "facebook.com",
    "fb.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "pinterest.com",
    "snapchat.com",
    "reddit.com",
    "tumblr.com",
    "whatsapp.com",
    "telegram.org",
    "discord.com",
    "twitch.tv",
    "vimeo.com",
    "flickr.com",
}

# Analytics & Tracking (no useful content)
ANALYTICS_TRACKING: Set[str] = {
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "facebook.net",
    "analytics.google.com",
    "facebook.com/tr",
    "connect.facebook.net",
    "pixel.facebook.com",
    "amplitude.com",
    "segment.com",
    "segment.io",
    "hotjar.com",
    "fullstory.com",
    "mixpanel.com",
    "quantcast.com",
    "scorecardresearch.com",
    "chartbeat.com",
}

# Ad Networks (no useful content, infinite redirects)
AD_NETWORKS: Set[str] = {
    "googlesyndication.com",
    "googleadservices.com",
    "adroll.com",
    "advertising.com",
    "adsense.google.com",
    "ads.google.com",
    "taboola.com",
    "outbrain.com",
    "criteo.com",
    "adform.com",
    "openx.net",
    "rubiconproject.com",
    "pubmatic.com",
}

# CDNs & Infrastructure (static files, not useful to crawl)
CDNS_INFRASTRUCTURE: Set[str] = {
    "cloudflare.com",
    "cloudfront.net",
    "akamai.net",
    "fastly.net",
    "jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
}

# Authentication & Login (requires credentials)
AUTH_LOGIN: Set[str] = {
    "accounts.google.com",
    "login.microsoftonline.com",
    "id.apple.com",
    "auth.amazon.com",
    "github.com/login",
    "gitlab.com/users/sign_in",
}

# Search Engines (infinite results, ToS issues)
SEARCH_ENGINES: Set[str] = {
    "google.com/search",
    "bing.com/search",
    "yahoo.com/search",
    "duckduckgo.com",
    "baidu.com",
    "yandex.com",
    "ask.com",
}

# E-commerce Platforms (infinite product listings, ToS issues)
ECOMMERCE_PLATFORMS: Set[str] = {
    "amazon.com",
    "ebay.com",
    "alibaba.com",
    "aliexpress.com",
    "walmart.com",
    "target.com",
    "shopify.com",
}

# File Sharing & Cloud Storage (authentication required, large files)
FILE_SHARING: Set[str] = {
    "drive.google.com",
    "dropbox.com",
    "onedrive.live.com",
    "box.com",
    "mega.nz",
    "mediafire.com",
    "wetransfer.com",
}

# Adult Content (NSFW, inappropriate for business crawling)
ADULT_CONTENT: Set[str] = {
    "pornhub.com",
    "xvideos.com",
    "xnxx.com",
    "redtube.com",
    "youporn.com",
    "xhamster.com",
    "tube8.com",
    "spankbang.com",
    "txxx.com",
    "eporner.com",
    "hqporner.com",
    "tnaflix.com",
    "drtuber.com",
    "keezmovies.com",
    "porntrex.com",
    "4tube.com",
    "faphouse.com",
    "onlyfans.com",
    "manyvids.com",
    "chaturbate.com",
    "stripchat.com",
    "cam4.com",
    "bongacams.com",
    "livejasmin.com",
    "myfreecams.com",
    "camsoda.com",
    "adultfriendfinder.com",
    "ashley-madison.com",
    "fling.com",
    "alt.com",
}

# ============================================================================
# COMBINED BLACKLIST
# ============================================================================

DOMAIN_BLACKLIST: Set[str] = (
    SOCIAL_MEDIA_DOMAINS
    | ANALYTICS_TRACKING
    | AD_NETWORKS
    | CDNS_INFRASTRUCTURE
    | AUTH_LOGIN
    | SEARCH_ENGINES
    | ECOMMERCE_PLATFORMS
    | FILE_SHARING
    | ADULT_CONTENT
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_domain_blacklisted(url: str) -> bool:
    """
    Check if a URL's domain is blacklisted.

    Args:
        url: Full URL to check

    Returns:
        True if domain is blacklisted, False otherwise

    Example:
        >>> is_domain_blacklisted("https://facebook.com/share")
        True
        >>> is_domain_blacklisted("https://example.com")
        False
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Check exact match
        if domain in DOMAIN_BLACKLIST:
            return True

        # Check if any blacklisted domain is in the URL
        # (e.g., "m.facebook.com" matches "facebook.com")
        for blacklisted_domain in DOMAIN_BLACKLIST:
            if domain.endswith(blacklisted_domain):
                return True
            if blacklisted_domain in domain:
                return True

        return False

    except Exception:
        # If parsing fails, err on the side of caution
        return True


def get_blacklist_reason(url: str) -> str:
    """
    Get the reason why a domain is blacklisted.

    Args:
        url: URL to check

    Returns:
        Reason string or empty string if not blacklisted
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        if domain in SOCIAL_MEDIA_DOMAINS:
            return "social_media"
        elif domain in ANALYTICS_TRACKING:
            return "analytics"
        elif domain in AD_NETWORKS:
            return "ads"
        elif domain in CDNS_INFRASTRUCTURE:
            return "cdn"
        elif domain in AUTH_LOGIN:
            return "authentication"
        elif domain in SEARCH_ENGINES:
            return "search_engine"
        elif domain in ECOMMERCE_PLATFORMS:
            return "ecommerce"
        elif domain in FILE_SHARING:
            return "file_sharing"
        elif domain in ADULT_CONTENT:
            return "adult_content"
        else:
            return ""

    except Exception:
        return "parse_error"


def get_blacklist_stats() -> dict:
    """
    Get statistics about the blacklist.

    Returns:
        Dictionary with category counts
    """
    return {
        "total_domains": len(DOMAIN_BLACKLIST),
        "social_media": len(SOCIAL_MEDIA_DOMAINS),
        "analytics": len(ANALYTICS_TRACKING),
        "ads": len(AD_NETWORKS),
        "cdn": len(CDNS_INFRASTRUCTURE),
        "auth": len(AUTH_LOGIN),
        "search_engines": len(SEARCH_ENGINES),
        "ecommerce": len(ECOMMERCE_PLATFORMS),
        "file_sharing": len(FILE_SHARING),
        "adult_content": len(ADULT_CONTENT),
    }


# ============================================================================
# CUSTOM BLACKLIST (User-Configurable)
# ============================================================================

# Users can add their own domains here or via environment variable
CUSTOM_BLACKLIST: Set[str] = set()

def add_to_blacklist(domain: str):
    """Add a domain to the custom blacklist."""
    CUSTOM_BLACKLIST.add(domain.lower())
    DOMAIN_BLACKLIST.add(domain.lower())


def remove_from_blacklist(domain: str):
    """Remove a domain from the custom blacklist."""
    domain = domain.lower()
    if domain in CUSTOM_BLACKLIST:
        CUSTOM_BLACKLIST.remove(domain)
    if domain in DOMAIN_BLACKLIST:
        DOMAIN_BLACKLIST.remove(domain)