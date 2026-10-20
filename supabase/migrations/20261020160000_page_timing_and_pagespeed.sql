-- Honest performance data for the report.
--
-- Why (2026-10-20): the report flagged seven cushlabs.ai pages as "slow" or
-- "critical" while Lighthouse scored the site in the high 90s. The only
-- number the crawler stored was pages.response_time: one fetch from our
-- Ashburn VPS, including the apex->www redirect, the body download and the
-- decode, taken while our own link checker was hitting the same host. That
-- is not a measure of what a visitor experiences and it was presented as one.
--
-- pages.final_url      where the request actually landed (after redirects).
-- pages.ttfb_ms        time to first byte of the final response, median of
--                      the samples below; the metric the report grades, on
--                      Google's own bands (good < 800 ms, poor > 1800 ms).
-- pages.redirect_ms    time spent in redirect hops before the final URL.
-- pages.ttfb_samples   every TTFB sample taken (first fetch + re-samples at
--                      the end of the crawl with the link checker idle).
-- crawls.pagespeed     Google PageSpeed Insights (Lighthouse) results for the
--                      start page and top pages: the proven, visitor-side
--                      measurement the report now quotes for "performance".
--
-- All columns are nullable and additive; code that predates them ignores
-- them, so this is safe to apply before the matching deploy.

ALTER TABLE pages
  ADD COLUMN IF NOT EXISTS final_url TEXT,
  ADD COLUMN IF NOT EXISTS ttfb_ms INTEGER,
  ADD COLUMN IF NOT EXISTS redirect_ms INTEGER,
  ADD COLUMN IF NOT EXISTS ttfb_samples JSONB;

COMMENT ON COLUMN pages.final_url IS 'URL the fetch landed on after redirects. NULL for rows crawled before 2026-10-20.';
COMMENT ON COLUMN pages.ttfb_ms IS 'Server time to first byte for final_url in ms, median of ttfb_samples, measured from the crawler host (US-East). Graded on Google TTFB bands.';
COMMENT ON COLUMN pages.redirect_ms IS 'Milliseconds spent on redirect hops before final_url on the first fetch. 0 when the URL did not redirect.';
COMMENT ON COLUMN pages.ttfb_samples IS 'JSON array of every TTFB sample in ms (first fetch plus end-of-crawl re-samples).';

ALTER TABLE crawls
  ADD COLUMN IF NOT EXISTS pagespeed JSONB;

COMMENT ON COLUMN crawls.pagespeed IS 'Google PageSpeed Insights (Lighthouse) results: {source, fetched_at, results: [{url, strategy, performance_score, lcp_ms, cls, tbt_ms, fcp_ms, speed_index_ms, server_response_ms, field: {...}|null}], errors: [...]}. NULL when not run.';
