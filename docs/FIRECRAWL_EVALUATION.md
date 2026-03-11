# FireCrawl Evaluation — AI WebScraper

> **Date**: 2026-03-10
> **Decision**: Not adopting FireCrawl. Custom crawler retained.
> **Revisit**: When anti-bot bypass becomes a blocking issue (v2+).

---

## What is FireCrawl?

FireCrawl is an API service (firecrawl.dev) that transforms websites into LLM-ready markdown. It handles proxy rotation, anti-bot bypass, JavaScript rendering, and clean content extraction. Used by 350,000+ developers including Shopify, Zapier, and Replit.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Scrape** | Extract content from any URL as markdown, HTML, or structured JSON |
| **Crawl** | Crawl entire sites and return all pages in LLM-ready format |
| **Map** | Get all URLs from a website (fast sitemap-like discovery) |
| **Search** | Web search with full page content from results |
| **Extract** | AI-powered structured data extraction from pages or entire sites |
| **Browser Sandbox** | Managed Chromium environments for interactive workflows |

### Pricing (as of March 2026)

| Plan | Monthly Cost | Credits | Concurrent Requests | Extra Credits |
|------|-------------|---------|---------------------|---------------|
| Free | $0 (one-time) | 500 | 2 | N/A |
| Hobby | $16/mo | 3,000 | 5 | $9/1,000 |
| Standard | $83/mo | 100,000 | 50 | $47/35,000 |
| Growth | $333/mo | 500,000 | 100 | $177/175,000 |
| Scale | $599/mo | 1,000,000 | 150 | Custom |
| Enterprise | Custom | Custom | Custom | Bulk discounts |

**Credit costs**: 1 credit/page for scrape/crawl, 2 credits/10 results for search, 2 credits/minute for browser sandbox.

---

## Head-to-Head Comparison

| Capability | Our Custom Crawler | FireCrawl API |
|---|---|---|
| **JS Rendering** | Playwright (self-hosted) | Managed Chromium |
| **Anti-bot Bypass** | None (custom User-Agent only) | Built-in proxy rotation, CAPTCHA handling |
| **Output Format** | Raw HTML + BeautifulSoup parsing | Clean markdown, structured JSON, screenshots |
| **SEO Issue Detection** | 11 custom checks | None |
| **AI Reports** | GPT-4 via Instructor with Pydantic | None |
| **Navigation Detection** | Custom NavDetector with scoring | None |
| **Domain Blacklisting** | 200+ domains across 9 categories | None |
| **Tier System** | Built-in (Free/Admin) | Their tier system, not ours |
| **Cost per page** | ~$0 (self-hosted) | $0.0008-0.005/page |
| **Rate Limiting** | Configurable 0.1-10 RPS | Platform limits (2-100 concurrent) |
| **Data Ownership** | 100% in our Supabase | Passes through their servers |
| **Offline/Local** | Yes | No |

---

## Why We're Not Switching

### 1. Our value is in the analysis, not the crawling

FireCrawl replaces only the page-fetching layer (~30% of our backend). Our differentiators — SEO issue detection (11 checks), AI-powered reports, navigation scoring, domain blacklisting, tier-based access — are all custom logic that FireCrawl doesn't provide. We'd still need all of that code.

### 2. Cost at scale breaks the business model

Our free tier gives users 3 crawls of up to 100 pages = 300 pages per free user at $0 cost. At FireCrawl's Hobby tier ($16/mo for 3,000 credits), we'd cap out at ~10 free users/month before needing to upgrade. At Standard ($83/mo), we could handle ~333 free users. Self-hosted crawling costs $0 per page — the only cost is compute.

### 3. Loss of crawl behavior control

Our crawler has specific tuning that FireCrawl can't replicate:
- **NavDetector** prioritizes important pages by analyzing HTML structure and CSS patterns
- **Domain blacklist** (200+ domains) prevents runaway crawls into social media and ad networks
- **External link depth/count limits** prevent infinite crawling
- **Configurable rate limiting** (0.1-10 RPS) respects target servers

### 4. Data sovereignty

All crawl data stays in our Supabase instance with Row Level Security. FireCrawl requires sending target URLs through their servers, which adds a data processing layer we don't need.

---

## Where FireCrawl Could Help (Future)

### Anti-bot Fallback (v2 consideration)

Some sites aggressively block scrapers (Cloudflare challenges, CAPTCHAs, IP-based blocking). Our crawler has no proxy rotation or CAPTCHA solving. FireCrawl handles this well.

**Hybrid approach**: Try our crawler first. If a site returns 403/CAPTCHA, retry through FireCrawl's API as a fallback. This keeps costs near zero for most crawls while handling edge cases.

### Implementation sketch (if needed later)

```python
# In crawler.py — hypothetical fallback
async def fetch_with_fallback(self, url: str) -> Response:
    try:
        response = await self.client.get(url)
        if response.status_code == 403:
            raise BlockedError(url)
        return response
    except BlockedError:
        # Fallback to FireCrawl for blocked sites
        return await self.firecrawl_client.scrape(url)
```

**Estimated cost impact**: If 5-10% of pages need FireCrawl fallback, cost per crawl stays under $0.50 for a 100-page crawl.

---

## Decision Log

| Date | Decision | Reasoning |
|------|----------|-----------|
| 2026-03-10 | Do not adopt FireCrawl | Custom crawler provides all needed functionality at $0/page cost. Our value is in analysis, not fetching. |
| — | Revisit for v2 | Consider as anti-bot fallback when we encounter sites that block our crawler. |
