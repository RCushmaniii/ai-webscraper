"""
Pure helpers that turn stored timing and PageSpeed data into report lines.

Kept out of routes/analysis.py so they can be unit-tested without the
report pipeline. No I/O here.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.services.pagespeed import headline

# Lighthouse's own bands for the performance category score.
PSI_GOOD = 90
PSI_NEEDS_WORK = 50


def _host(url: str) -> str:
    return (urlparse(url or "").netloc or "").lower()


def redirect_findings(start_url: str, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One line if the start URL lands on another host; one line if crawled
    internal URLs redirect before serving (each hop costs every visitor)."""
    findings: List[Dict[str, Any]] = []

    start_page = next((p for p in pages if (p.get("depth") or 0) == 0 and p.get("final_url")), None)
    if start_page and _host(start_page["final_url"]) and _host(start_page["final_url"]) != _host(start_page.get("url", "")):
        hop_ms = start_page.get("redirect_ms") or 0
        findings.append({
            "category": "Technical",
            "severity": "low",
            "finding": (
                f'{start_page.get("url")} redirects to {start_page["final_url"]}'
                + (f" ({hop_ms} ms per visit)" if hop_ms else "")
                + "; use the final address in links, ads and listings so visitors skip the hop"
            ),
            "current_value": start_page["final_url"],
            "target": "Link straight to the canonical host",
            "url": start_page.get("url"),
        })

    redirected = [
        p for p in pages
        if (p.get("depth") or 0) > 0 and (p.get("redirect_ms") or 0) > 0
        and p.get("final_url") and p.get("final_url") != p.get("url")
    ]
    if redirected:
        avg = round(sum(p["redirect_ms"] for p in redirected) / len(redirected))
        findings.append({
            "category": "Technical",
            "severity": "low" if len(redirected) < 5 else "medium",
            "finding": (
                f"{len(redirected)} internal link target(s) redirect before serving "
                f"(about {avg} ms each); point internal links at the final URLs"
            ),
            "current_value": len(redirected),
            "target": "0 redirecting internal links",
            "url": redirected[0].get("url"),
        })
    return findings


def _fmt_ms(ms: Optional[int]) -> str:
    if ms is None:
        return "n/a"
    return f"{ms / 1000:.1f} s" if ms >= 1000 else f"{ms} ms"


def pagespeed_findings(pagespeed: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """A finding per audited page whose Lighthouse performance score is below
    90 (Lighthouse's own 'good' threshold); nothing when the site is fine."""
    findings: List[Dict[str, Any]] = []
    if not pagespeed:
        return findings
    for r in pagespeed.get("results") or []:
        score = r.get("performance_score")
        if score is None or score >= PSI_GOOD:
            continue
        parts = []
        if r.get("lcp_ms") is not None:
            parts.append(f"LCP {_fmt_ms(r['lcp_ms'])}")
        if r.get("cls") is not None:
            parts.append(f"CLS {r['cls']}")
        if r.get("tbt_ms") is not None:
            parts.append(f"TBT {_fmt_ms(r['tbt_ms'])}")
        findings.append({
            "category": "Performance",
            "severity": "high" if score < PSI_NEEDS_WORK else "medium",
            "finding": (
                f'Google PageSpeed ({r.get("strategy")}) scores {r.get("url")} {score}/100'
                + (f" ({', '.join(parts)})" if parts else "")
            ),
            "current_value": score,
            "target": f"{PSI_GOOD}+ (Lighthouse 'good')",
            "url": r.get("url"),
        })
    return findings


def pagespeed_summary_text(pagespeed: Optional[Dict[str, Any]]) -> str:
    """Lines for the AI narrative. Lighthouse is the performance authority;
    the prompt tells the model so."""
    if not pagespeed or not pagespeed.get("results"):
        return "Not available for this crawl."
    lines = []
    for r in pagespeed["results"]:
        bits = [f"{r.get('strategy')} {r.get('url')}: {r.get('performance_score')}/100"]
        if r.get("lcp_ms") is not None:
            bits.append(f"LCP {_fmt_ms(r['lcp_ms'])}")
        if r.get("cls") is not None:
            bits.append(f"CLS {r['cls']}")
        if r.get("tbt_ms") is not None:
            bits.append(f"TBT {_fmt_ms(r['tbt_ms'])}")
        field = r.get("field")
        if field:
            bits.append(f"real-user Chrome data: {field.get('overall_category', '').lower() or 'available'}")
        lines.append("- " + ", ".join(bits))
    head = headline(pagespeed)
    if head and head.get("performance_score") is not None:
        lines.insert(0, f"Headline: start page mobile {head['performance_score']}/100.")
    return "\n".join(lines)
