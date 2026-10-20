"""
Server response time is graded on Google's TTFB bands from a median of
samples, Lighthouse is the performance authority, and the crawler measures
TTFB/redirects/total separately against the final URL.

Background (2026-10-20): a report called seven cushlabs.ai pages "slow" or
"critical" from one whole-fetch reading per page taken through an apex->www
redirect while our own link checker hit the host; Lighthouse scored the same
site 97/100.
"""

import asyncio
import json

import httpx
import pytest
from unittest.mock import MagicMock

from app.core.performance import (
    STATUS_PASS,
    STATUS_POOR,
    STATUS_SLOW,
    classify_ttfb,
    median_ms,
    page_response_ms,
    response_metric_name,
    sample_count,
)
from app.services import pagespeed
from app.services.report_findings import (
    pagespeed_findings,
    pagespeed_summary_text,
    redirect_findings,
)


class TestBands:
    def test_google_ttfb_bands(self):
        assert classify_ttfb(799) == STATUS_PASS
        assert classify_ttfb(800) == STATUS_SLOW
        assert classify_ttfb(1799) == STATUS_SLOW
        assert classify_ttfb(1800) == STATUS_POOR
        assert classify_ttfb(3788) == STATUS_POOR

    def test_nothing_measured_is_not_graded(self):
        assert classify_ttfb(None) == STATUS_PASS
        assert classify_ttfb(0) == STATUS_PASS

    def test_median_ignores_missing(self):
        assert median_ms([3788, 310, None, 290]) == 310
        assert median_ms([]) is None

    def test_page_prefers_ttfb_over_whole_fetch(self):
        page = {"response_time": 3788, "ttfb_ms": 310, "ttfb_samples": [3100, 310, 290]}
        assert page_response_ms(page) == 310
        assert response_metric_name(page) == "ttfb"
        assert sample_count(page) == 3

    def test_old_rows_fall_back_to_fetch_time(self):
        page = {"response_time": 1346}
        assert page_response_ms(page) == 1346
        assert response_metric_name(page) == "fetch"
        assert sample_count(page) == 1


PSI_RAW = {
    "lighthouseResult": {
        "lighthouseVersion": "12.2.1",
        "categories": {"performance": {"score": 0.97}},
        "audits": {
            "first-contentful-paint": {"numericValue": 912.4},
            "largest-contentful-paint": {"numericValue": 1240.0},
            "total-blocking-time": {"numericValue": 30.0},
            "speed-index": {"numericValue": 1500.0},
            "cumulative-layout-shift": {"numericValue": 0.0123},
            "server-response-time": {"numericValue": 210.0},
        },
    },
    "loadingExperience": {
        "overall_category": "FAST",
        "metrics": {
            "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 1800},
            "INTERACTION_TO_NEXT_PAINT": {"percentile": 120},
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": {"percentile": 2},
            "EXPERIMENTAL_TIME_TO_FIRST_BYTE": {"percentile": 400},
        },
    },
}


class TestPageSpeed:
    def test_summarize_reduces_to_report_fields(self):
        out = pagespeed.summarize("https://www.cushlabs.ai/", "mobile", PSI_RAW)
        assert out["performance_score"] == 97
        assert out["lcp_ms"] == 1240 and out["fcp_ms"] == 912 and out["tbt_ms"] == 30
        assert out["cls"] == 0.012
        assert out["server_response_ms"] == 210
        assert out["field"] == {
            "overall_category": "FAST", "lcp_ms": 1800, "inp_ms": 120, "cls": 0.02, "ttfb_ms": 400,
        }

    def test_summarize_without_field_data(self):
        raw = {"lighthouseResult": PSI_RAW["lighthouseResult"], "loadingExperience": {"metrics": {}}}
        out = pagespeed.summarize("https://x.example/", "desktop", raw)
        assert out["field"] is None
        assert out["performance_score"] == 97

    def test_run_sends_key_and_params(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(dict(request.url.params))
            return httpx.Response(200, json=PSI_RAW)

        async def go():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await pagespeed.run_pagespeed(client, "https://www.cushlabs.ai/", "mobile", "k-test")

        out = asyncio.run(go())
        assert seen == {"url": "https://www.cushlabs.ai/", "strategy": "mobile", "category": "performance", "key": "k-test"}
        assert out["performance_score"] == 97

    def test_for_urls_never_raises_and_orders_start_first(self, monkeypatch):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            url = request.url.params["url"]
            calls.append((url, request.url.params["strategy"]))
            if "broken" in url:
                return httpx.Response(500, json={"error": {"message": "Lighthouse returned error: ERRORED_DOCUMENT_REQUEST"}})
            return httpx.Response(200, json=PSI_RAW)

        real_client = httpx.AsyncClient

        class PatchedClient(real_client):
            def __init__(self, *a, **kw):
                kw["transport"] = httpx.MockTransport(handler)
                super().__init__(*a, **kw)

        monkeypatch.setattr(pagespeed.httpx, "AsyncClient", PatchedClient)
        out = asyncio.run(pagespeed.pagespeed_for_urls(
            "https://www.cushlabs.ai/",
            ["https://www.cushlabs.ai/pricing/", "https://www.cushlabs.ai/broken/", "https://www.cushlabs.ai/"],
            api_key="",
        ))
        assert [(r["url"], r["strategy"]) for r in out["results"]] == [
            ("https://www.cushlabs.ai/", "mobile"),
            ("https://www.cushlabs.ai/", "desktop"),
            ("https://www.cushlabs.ai/pricing/", "mobile"),
        ]
        assert len(out["errors"]) == 1 and "ERRORED_DOCUMENT_REQUEST" in out["errors"][0]
        assert out["keyed"] is False
        # The start URL repeated in extra_urls is not audited twice.
        assert len(calls) == 4

    def test_merge_keeps_start_page_first(self):
        a = {"fetched_at": "2026-10-20T16:00:00+00:00", "keyed": True,
             "results": [{"url": "https://s/", "strategy": "mobile", "performance_score": 97},
                         {"url": "https://s/", "strategy": "desktop", "performance_score": 99}],
             "errors": []}
        b = {"fetched_at": "2026-10-20T16:02:00+00:00", "keyed": True,
             "results": [{"url": "https://s/a/", "strategy": "mobile", "performance_score": 80}],
             "errors": ["mobile https://s/b/: boom"]}
        merged = pagespeed.merge_pagespeed(a, b)
        assert [r["url"] for r in merged["results"]] == ["https://s/", "https://s/", "https://s/a/"]
        assert merged["fetched_at"] == b["fetched_at"]
        assert merged["errors"] == ["mobile https://s/b/: boom"]
        assert pagespeed.merge_pagespeed(None, None) is None
        assert pagespeed.headline(merged)["performance_score"] == 97


class TestFindings:
    PAGES = [
        {"url": "https://cushlabs.ai/", "final_url": "https://www.cushlabs.ai/", "depth": 0, "redirect_ms": 240},
        {"url": "https://www.cushlabs.ai/pricing/", "final_url": "https://www.cushlabs.ai/pricing/", "depth": 1, "redirect_ms": 0},
        {"url": "https://www.cushlabs.ai/old/", "final_url": "https://www.cushlabs.ai/new/", "depth": 1, "redirect_ms": 180},
    ]

    def test_start_url_redirect_and_internal_redirects(self):
        out = redirect_findings("https://cushlabs.ai/", self.PAGES)
        assert len(out) == 2
        assert "redirects to https://www.cushlabs.ai/" in out[0]["finding"] and out[0]["severity"] == "low"
        assert "1 internal link target(s) redirect" in out[1]["finding"]

    def test_no_redirects_no_findings(self):
        pages = [{"url": "https://www.x/", "final_url": "https://www.x/", "depth": 0, "redirect_ms": 0}]
        assert redirect_findings("https://www.x/", pages) == []

    def test_pagespeed_finding_only_when_below_good(self):
        ps = {"results": [
            {"url": "https://s/", "strategy": "mobile", "performance_score": 97, "lcp_ms": 1240, "cls": 0.01, "tbt_ms": 30},
            {"url": "https://s/heavy/", "strategy": "mobile", "performance_score": 44, "lcp_ms": 6100, "cls": 0.31, "tbt_ms": 900},
        ]}
        out = pagespeed_findings(ps)
        assert len(out) == 1
        assert out[0]["severity"] == "high" and "44/100" in out[0]["finding"] and "LCP 6.1 s" in out[0]["finding"]
        assert pagespeed_findings(None) == []

    def test_summary_text_leads_with_headline(self):
        text = pagespeed_summary_text({"results": [
            {"url": "https://s/", "strategy": "mobile", "performance_score": 97, "lcp_ms": 1240, "cls": 0.01},
        ]})
        assert text.startswith("Headline: start page mobile 97/100.")
        assert pagespeed_summary_text(None) == "Not available for this crawl."


class TestCrawlerTiming:
    @pytest.fixture
    def crawler_with_transport(self, make_crawler):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "cushlabs.ai":
                return httpx.Response(308, headers={"location": str(request.url.copy_with(host="www.cushlabs.ai"))})
            if request.url.path == "/blocked":
                return httpx.Response(429, headers={"retry-after": "30"})
            return httpx.Response(200, headers={"content-type": "text/html"}, html="<html><body>ok</body></html>")

        crawler = make_crawler(url="https://cushlabs.ai/")
        crawler.client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
        return crawler

    def test_www_and_apex_are_the_same_site(self, make_crawler):
        crawler = make_crawler(url="https://cushlabs.ai/")
        assert crawler._is_internal_host("www.cushlabs.ai")
        assert crawler._is_internal_host("CUSHLABS.AI")
        assert not crawler._is_internal_host("scraper.cushlabs.ai")

    def test_redirect_target_becomes_internal(self, make_crawler):
        crawler = make_crawler(url="https://old-brand.example/")
        assert not crawler._is_internal_host("new-brand.example")
        crawler._learn_internal_host("https://new-brand.example/home/")
        assert crawler._is_internal_host("new-brand.example")
        assert crawler._is_internal_host("www.new-brand.example")

    def test_timed_get_separates_redirect_from_ttfb(self, crawler_with_transport):
        crawler = crawler_with_transport
        response, timing = asyncio.run(crawler._timed_get("https://cushlabs.ai/pricing/"))
        assert str(response.url) == "https://www.cushlabs.ai/pricing/"
        assert response.text.startswith("<html>")
        assert len(response.history) == 1
        assert timing["redirect_ms"] >= 0
        assert timing["ttfb_ms"] >= 0
        assert timing["total_ms"] >= timing["ttfb_ms"]

    def test_ttfb_only_stops_on_block(self, crawler_with_transport):
        crawler = crawler_with_transport
        assert asyncio.run(crawler._ttfb_only("https://www.cushlabs.ai/fine")) is not None
        assert crawler.blocked_reason is None
        assert asyncio.run(crawler._ttfb_only("https://www.cushlabs.ai/blocked")) is None
        assert "429" in crawler.blocked_reason

    def test_resample_stores_median_of_three(self, crawler_with_transport, monkeypatch):
        import app.services.crawler as crawler_module
        crawler = crawler_with_transport
        monkeypatch.setattr(crawler_module, "RESAMPLE_IDLE_S", 0)
        crawler.page_timings = [{"page_id": "p1", "url": "https://www.cushlabs.ai/pricing/", "ttfb_ms": 3100}]

        updates = []
        crawler.db = MagicMock()
        crawler.db.table.return_value.update.side_effect = lambda data: updates.append(data) or crawler.db.table.return_value
        asyncio.run(crawler._resample_response_times())

        assert len(updates) == 1
        assert len(updates[0]["ttfb_samples"]) == 3
        assert updates[0]["ttfb_samples"][0] == 3100
        # Two fast re-samples outweigh the one slow mid-crawl reading.
        assert updates[0]["ttfb_ms"] < 3100
