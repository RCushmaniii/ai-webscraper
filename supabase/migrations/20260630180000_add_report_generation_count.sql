-- Add a per-crawl report generation counter to cap AI report spend.
--
-- Why: the app is publicly reachable. Without a cap, a malicious (or merely
-- curious) free-tier user can repeatedly re-trigger AI report generation on a
-- single crawl and burn the owner's OpenAI budget. The report is already cached
-- in `ai_report`, so legitimate viewing costs nothing — only deliberate
-- regeneration spends money. This counter lets us hard-cap free-tier users at
-- FREE_REPORT_LIMIT generations per crawl (admins are exempt; see analysis.py).

ALTER TABLE crawls
ADD COLUMN IF NOT EXISTS report_generation_count INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN crawls.report_generation_count IS
  'Number of times an AI report has been generated for this crawl. Enforced server-side: free-tier users are capped (FREE_REPORT_LIMIT in analysis.py); admins are exempt.';
