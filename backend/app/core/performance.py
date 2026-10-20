"""
How the report grades server response time, in one place.

Why (2026-10-20): the report called a 1,346 ms single fetch "slow" and a
3,788 ms one "critical" and said so in the findings, while Google's own
Lighthouse scored the same site in the high 90s. The old bands (1 s / 3 s)
were applied to one reading that included a redirect hop, the body download
and our own crawler's load on the host. The bands below are Google's
published time-to-first-byte guidance (web.dev/articles/ttfb): good under
800 ms, needs improvement under 1,800 ms, poor above. They are applied to a
median of several TTFB samples taken against the final URL, and the result
is never called "critical": a one-location server reading is not a verdict
on the site, and real visitor-side performance comes from PageSpeed
Insights (see app/services/pagespeed.py).
"""

from statistics import median
from typing import Iterable, Optional

TTFB_GOOD_MS = 800
TTFB_POOR_MS = 1800

# Status values are part of the report contract (frontend PageAuditTab,
# CSV/PDF export, summary_stats.performance_pass_rate).
STATUS_PASS = "pass"
STATUS_SLOW = "slow"
STATUS_POOR = "poor"

TTFB_TARGET_TEXT = f"Under {TTFB_GOOD_MS} ms (Google TTFB guidance)"
MEASUREMENT_NOTE = "server time to first byte, measured from our US-East server"


def classify_ttfb(ms: Optional[float]) -> str:
    """Google's TTFB bands. ``None``/0 (nothing measured) counts as pass so an
    old crawl without the column is not graded on missing data."""
    if not ms or ms <= 0:
        return STATUS_PASS
    if ms < TTFB_GOOD_MS:
        return STATUS_PASS
    if ms < TTFB_POOR_MS:
        return STATUS_SLOW
    return STATUS_POOR


def median_ms(samples: Iterable[Optional[float]]) -> Optional[int]:
    """Median of the measured samples (None = not measured), or None."""
    values = [float(s) for s in samples if s is not None and s >= 0]
    if not values:
        return None
    return int(round(median(values)))


def page_response_ms(page: dict) -> int:
    """The number the report grades for a page row.

    Prefers the median TTFB (crawls since 2026-10-20); falls back to the old
    whole-fetch ``response_time`` for older crawls, which over-reports and is
    labelled as such by ``response_metric_name``.
    """
    ttfb = page.get("ttfb_ms")
    if ttfb is not None and ttfb > 0:
        return int(ttfb)
    return int(page.get("response_time") or 0)


def response_metric_name(page: dict) -> str:
    return "ttfb" if page.get("ttfb_ms") else "fetch"


def sample_count(page: dict) -> int:
    samples = page.get("ttfb_samples")
    if isinstance(samples, list) and samples:
        return len(samples)
    return 1
