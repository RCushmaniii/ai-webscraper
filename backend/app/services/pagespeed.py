"""
Google PageSpeed Insights (Lighthouse) for the pages that matter.

Why (2026-10-20): the report's "performance" findings came from one HTTP
fetch per page from our own server and contradicted Lighthouse completely.
PageSpeed Insights is Lighthouse run by Google, from Google's infrastructure,
with field data from real Chrome users when the site has enough traffic. It
is free (25,000 queries/day with an API key, a handful per minute without),
and it is the number a site owner will check us against.

What runs per crawl: the start page on mobile and desktop, plus up to
MAX_EXTRA_PAGES primary pages on mobile. Each call takes Google 10-30 s;
calls run with a small concurrency and never fail the crawl.

Stored on crawls.pagespeed as the dict ``pagespeed_for_urls`` returns.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
SOURCE = "Google PageSpeed Insights (Lighthouse)"
MAX_EXTRA_PAGES = 3
CONCURRENCY = 2
TIMEOUT_S = 90.0

# Lighthouse audit ids -> our keys. Values are milliseconds except CLS.
_AUDIT_KEYS = {
    "first-contentful-paint": "fcp_ms",
    "largest-contentful-paint": "lcp_ms",
    "total-blocking-time": "tbt_ms",
    "speed-index": "speed_index_ms",
    "server-response-time": "server_response_ms",
}


def _ms(value: Any) -> Optional[int]:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def summarize(url: str, strategy: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce a PSI response to what the report shows. Pure; tested."""
    lh = raw.get("lighthouseResult") or {}
    audits = lh.get("audits") or {}
    categories = lh.get("categories") or {}
    score = (categories.get("performance") or {}).get("score")

    out: Dict[str, Any] = {
        "url": url,
        "strategy": strategy,
        "performance_score": int(round(score * 100)) if isinstance(score, (int, float)) else None,
        "lighthouse_version": lh.get("lighthouseVersion"),
        "cls": None,
        "field": None,
    }
    for audit_id, key in _AUDIT_KEYS.items():
        out[key] = _ms((audits.get(audit_id) or {}).get("numericValue"))
    cls = (audits.get("cumulative-layout-shift") or {}).get("numericValue")
    if isinstance(cls, (int, float)):
        out["cls"] = round(float(cls), 3)

    # Field data (Chrome UX Report) exists only for sites with enough traffic.
    field = raw.get("loadingExperience") or {}
    metrics = field.get("metrics") or {}
    if metrics and field.get("overall_category"):
        def pct(name: str) -> Optional[Any]:
            return (metrics.get(name) or {}).get("percentile")
        out["field"] = {
            "overall_category": field.get("overall_category"),
            "lcp_ms": _ms(pct("LARGEST_CONTENTFUL_PAINT_MS")),
            "inp_ms": _ms(pct("INTERACTION_TO_NEXT_PAINT")),
            "cls": round(pct("CUMULATIVE_LAYOUT_SHIFT_SCORE") / 100, 3)
            if isinstance(pct("CUMULATIVE_LAYOUT_SHIFT_SCORE"), (int, float)) else None,
            "ttfb_ms": _ms(pct("EXPERIMENTAL_TIME_TO_FIRST_BYTE")),
        }
    return out


async def run_pagespeed(
    client: httpx.AsyncClient, url: str, strategy: str, api_key: str = ""
) -> Dict[str, Any]:
    params = {"url": url, "strategy": strategy, "category": "performance"}
    if api_key:
        params["key"] = api_key
    response = await client.get(PSI_ENDPOINT, params=params, timeout=TIMEOUT_S)
    response.raise_for_status()
    return summarize(url, strategy, response.json())


async def pagespeed_for_urls(
    start_url: Optional[str],
    extra_urls: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Lighthouse for the start page (mobile + desktop) and a few top pages
    (mobile). ``start_url`` may be None to audit only ``extra_urls``.
    Never raises; failures are listed under ``errors``."""
    key = settings.PAGESPEED_API_KEY if api_key is None else api_key
    jobs: List[tuple] = []
    seen = set()
    if start_url:
        jobs += [(start_url, "mobile"), (start_url, "desktop")]
        seen.add(start_url.rstrip("/"))
    for u in extra_urls or []:
        if len(jobs) >= 2 + MAX_EXTRA_PAGES:
            break
        if u and u.rstrip("/") not in seen:
            seen.add(u.rstrip("/"))
            jobs.append((u, "mobile"))

    results: List[Dict[str, Any]] = []
    errors: List[str] = []
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient() as client:
        async def one(url: str, strategy: str) -> None:
            async with semaphore:
                try:
                    results.append(await run_pagespeed(client, url, strategy, key))
                except Exception as e:  # noqa: BLE001 - never fail the crawl
                    # PSI's own error body names the cause (quota, unreachable URL).
                    detail = ""
                    if isinstance(e, httpx.HTTPStatusError):
                        try:
                            detail = e.response.json().get("error", {}).get("message", "")
                        except Exception:  # noqa: BLE001
                            detail = e.response.text[:200]
                    errors.append(f"{strategy} {url}: {type(e).__name__} {detail or e}".strip())
                    logger.warning("PageSpeed failed for %s (%s): %s", url, strategy, detail or e)

        await asyncio.gather(*(one(u, s) for u, s in jobs))

    return {
        "source": SOURCE,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "keyed": bool(key),
        "results": _ordered(results, start_url),
        "errors": errors,
    }


def _ordered(results: List[Dict[str, Any]], start_url: Optional[str]) -> List[Dict[str, Any]]:
    """Start page first (mobile before desktop), then the rest by URL."""
    order = {"mobile": 0, "desktop": 1}
    start = (start_url or "").rstrip("/")
    return sorted(
        results,
        key=lambda r: (r["url"].rstrip("/") != start, order.get(r["strategy"], 9), r["url"]),
    )


def merge_pagespeed(
    first: Optional[Dict[str, Any]], second: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Combine the start-page run with the top-pages run into one record."""
    parts = [p for p in (first, second) if p]
    if not parts:
        return None
    results: List[Dict[str, Any]] = []
    errors: List[str] = []
    for part in parts:
        results += part.get("results") or []
        errors += part.get("errors") or []
    start_url = None
    if first and first.get("results"):
        start_url = first["results"][0]["url"]
    return {
        "source": SOURCE,
        "fetched_at": max(p.get("fetched_at") or "" for p in parts),
        "keyed": any(p.get("keyed") for p in parts),
        "results": _ordered(results, start_url),
        "errors": errors,
    }


def headline(pagespeed: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The start page's mobile result, for summaries and the AI narrative."""
    if not pagespeed:
        return None
    for r in pagespeed.get("results") or []:
        if r.get("strategy") == "mobile":
            return r
    results = pagespeed.get("results") or []
    return results[0] if results else None
