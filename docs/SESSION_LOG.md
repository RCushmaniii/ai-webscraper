# Session Log — ai-webscraper

Entries are newest-first. Each entry documents one Claude Code working session.

---

## Session: 2026-07-06 (Sentry wiring verified + noise reduction)

### Accomplished

- **Verified both Sentry projects end-to-end.** Backend (`backend-cushlabs-ai-webscraper`, id `4511164689022976`): fired a `capture_message` from the container → landed. Frontend (`frontent-cushlabs-ai-scraper`, id `4511164603170816`): drove the live site with Playwright, threw an uncaught error → SDK POSTed to the correct project, HTTP 200, no CSP block. Both DSNs confirmed correct in local `.env`, prod `.env.webscraper`, and the deployed bundle.
- **Clarified `SENTRY_SECURITY_TOKEN` is unused** — it's Sentry's legacy CSP token, not the DSN; error reporting was already correctly wired via DSN.
- **Shipped PR #92 (merged, deployed, verified live)** — Sentry noise reduction + two bug fixes:
  - `before_send` filter drops transient network/DNS errors; background loops rewritten (`_guarded_periodic`) so blips log at WARNING and a sustained outage emits exactly ONE event (fixes the 851-event `Name or service not known` flood, `BACKEND-…-4`).
  - Audit writes now use a service-role client instead of the anon-key singleton (`audit.py`), fixing RLS `42501` (`BACKEND-…-9`) — verified live with a self-cleaning insert.
  - Crawl deletion deletes `seo_metadata` by `page_id` not `crawl_id`, fixing `42703` (`BACKEND-…-A`) — verified live.
  - New `tests/test_sentry_filtering.py` (8 tests); full suite 111 passed.
- **Enabled Auto-Resolve (30d) on both projects and cleared stale issues** (Robert, dashboard).

### Decisions Made

- Filter transient net/DNS errors rather than tune sample rates: the noise was error-events from `logger.error` in loops, not tracing volume.
- Sustained outages still surface (1 gated event, no `exc_info` so it passes `before_send`) — infra visibility kept without per-loop spam.

### Immediate Next Steps

- [ ] Rotate or remove the dead `SENTRY_AUTH_TOKEN` in `backend/.env`/`frontend/.env` (returns 401 "Invalid org token"; unused since the build uploads no source maps).
- [ ] Fix pre-existing frontend TS error failing CI type-check: `frontend/src/pages/CrawlDetailPage.tsx:576` (`'desc'` vs `'asc'` comparison, no overlap).

### Technical Debt

- Connected Sentry MCP is scoped to `cushlabs-marketsignal`, not this app — can't query/resolve ai-webscraper issues via MCP; use the dashboard or a valid user auth token.

### Open Questions / Blockers

- None.

---

## Session: 2026-07-01 (rate limiting activated — Upstash Redis)

### Accomplished

- **Found the rate limiter was completely inert in production** (PR #91). `rate_limit_middleware` keyed off `request.state.user_id`, which nothing ever set (auth lives in `contextvars`), so every request bypassed it. The Redis limiter was also a `NotImplementedError` stub → the API had no rate limiting at all.
- **Implemented `UpstashRateLimiter`** (REST, async) with a fixed-window `INCR`+`EXPIRE` counter — distributed and restart-safe. Fixed the middleware to identify callers from the JWT `sub` claim (falls back to `X-Forwarded-For` IP behind Caddy), scoped to mutating `/api/v1` endpoints only. Fails **open** on limiter errors; feature-flagged off until Upstash env vars present.
- **Provisioned Upstash** (Regional, us-east-1 to match the Virginia VPS). Pushed `UPSTASH_REDIS_REST_URL`/`TOKEN` into `~/apps/cushlabs-prod-server/.env.webscraper` via a `node --env-file` script (values over SSH stdin, never in chat) after copy-paste quoting mangled them twice.
- **Deployed and verified live** on `scraper.cushlabs.ai`: 13 rapid POSTs → 10×`403` then `429` (exact 10/min boundary); 13 GETs → all `200` (reads never throttled). Confirms wiring fixed, Upstash counting, targeting correct.
- **Corrected stale deploy docs in `CLAUDE.md`** — the box no longer builds (`--build`); CI builds → GHCR, box `docker compose pull`. This drift caused most of the friction this session.

### Decisions Made

- Upstash over local Redis container: user chose it for fleet consistency + zero ops/RAM on the 4GB VPS (accepted the per-request REST round-trip, mitigated by only limiting writes).
- Scope to writes only (no GET throttling): avoids false 429s on SPA navigation and skips a remote round-trip on read traffic.
- Fail-open: a limiter/Upstash outage degrades to "allow", never a lockout.

### Immediate Next Steps

- [ ] Implement real `get_tier_from_user()` (still hardcoded FREE) when billing/Stripe lands — PRO/ENTERPRISE limits already defined in `rate_limits.py`.

### Technical Debt

- Monthly-crawl / concurrent-crawl limit helpers in `rate_limiter.py` are still stubbed (`current_count = 0`); monthly cap is DB-enforced via `FREE_CRAWL_LIMIT` for now.
- The secrets-guard hook repeatedly blocked benign `echo`/`git check-ignore` lines that merely mentioned `.env.webscraper`; workable but noisy.

### Open Questions / Blockers

- None.

---

## Session: 2026-06-30 (PM — outage recovery + report authenticity)

### Accomplished

- **Production outage fixed:** re-crawls saved 0 pages. Root cause: PR #82 added code writing/reading `pages.word_count` but no migration created the column → every insert threw 42703. Added `20260630183000_add_word_count_to_pages.sql`, applied; verified all 24 crawler insert columns now exist (PR #85).
- **Silent-success guard (PR #86):** crawler now tracks `pages_saved`/`pages_save_failed` separately from `pages_crawled` (fetches). Worker marks `failed` when 0 saved (vs. lying "completed/10 pages"), warns on partial save, gates issue-detection/SEO-audit on `pages_saved > 0`. Frontend renders `crawl.error` banner (red=failed, amber=partial) — the field existed but was never shown.
- **Report authenticity overhaul** (the "feels fake" fix, root-cause not prompt-nudge):
  - **Earned scores (PR #88):** the 5 scores were LLM-generated → lazy 100s. Now `compute_health_scores()` computes them deterministically and OVERRIDES the model (granular & absolute). Verified clean=100, messy=39.
  - **Anti-fabrication (PR #88):** killed the hallucinated "strategic score of 81" + invented "20-30% conversion" stats. Rewrote the model field descriptions that _taught_ fabrication; added hard EVIDENCE-BOUND rule + banned phrases. Quick wins now evidence-bound (clean site → zero, no CTA padding).
  - **Score consistency (PR #89):** folded schema/internal-linking/strategy sub-scores into the 4 pillars (weight-renormalizing `_blend`, falls back gracefully). cushlabs now reads 96/96/95/100/95 — headline matches body (Schema 73 visibly pulls Technical/Trust down) instead of a flat-100 gloss.
- **Copy-section button (PR #90):** serializes the whole Strategy & Conversion Analysis to plain text for pasting into an AI assistant.
- Validated end-to-end on cushlabs.ai: Robert confirms the report now reads natural, accurate, internally consistent.

### Decisions Made

- Earned-but-absolute scoring (Robert's pick): a flawless site can still hit 100, but real gaps deduct. Scores moved to code because a score is measurement, not an intelligence task — the AI still owns all strategy/narrative.
- Used existing `failed` status for save failures rather than a new `completed_with_errors` enum (would need a CHECK-constraint migration + every `status==='completed'` gate touched).
- Continued cleaning prettier's wholesale frontend reformat each time (restore HEAD + reapply functional hunks via perl/python) to keep PR diffs tight.

### Immediate Next Steps

- [ ] Rotate the `SENTRY_AUTH_TOKEN` (exposed in chat 2026-06-28) — still outstanding.
- [ ] (Optional) Verify the report-generation 429 cap with a real free-tier account.

### Technical Debt

- Per-page audit scoring leniency is untouched — `avg_page_score` still feeds Content; could tighten thresholds later.
- Pre-existing `tsc` error in `CrawlDetailPage.tsx` (sort-direction comparison) — not blocking Vite build.
- Caddyfile CSP edits live only on the VPS, not version-controlled.

### Open Questions / Blockers

- None.

---

## Session: 2026-06-30 (AM — prompt sharpening + report cap)

### Accomplished

- Sharpened executive-summary LLM prompts (PR #83): quick wins must DIVERSIFY across issue types ("five near-identical fixes is a FAIL"); strategic recs must connect 2+ findings + name a URL/page/number; banned generic titles ("Address core SEO foundations"); added accessible/action-oriented directive. `llm_service.py:659`, `llm_models.py`.
- Capped AI report generation at 2 per crawl for free-tier users; admins exempt (PR #84). Server-enforced (429), not just UI — a disabled button can't stop a direct API call.
  - Migration `20260630180000_add_report_generation_count.sql` (int, default 0); applied to remote via `supabase db push`.
  - `POST/GET /report` now return `report_generation_count` / `report_limit` / `can_regenerate`; POST increments counter + returns GET's wrapper shape. `analysis.py` `FREE_REPORT_LIMIT = 2`.
  - Frontend: Regenerate button disables w/ tooltip once capped (`ReportPanel.tsx`, `CrawlDetailPage.tsx`, `api.ts`).
- Deployed both: CI built GHCR image → VPS pulled `:latest` + recreated container (health 200, cap code verified live); frontend `scp`'d to VPS.

### Decisions Made

- Report cap over auto-generate/confirm-dialog: public app + abuse vector ("not my money") justifies a hard server-side cap; admins exempt so prompt iteration stays unblocked. Free-tier worst case = 3 crawls × 2 reports = 6 generations.
- Reverted prettier's wholesale reformat (~2,200 quote-churn lines) on the two touched frontend files; re-applied only functional hunks via `git apply`/perl so the PR diff stayed 81/+6/- and blame history clean.

### Immediate Next Steps

- [ ] Verify the 429 + disabled Regenerate button end-to-end with a free-tier (non-admin) account (Robert testing; admin is exempt so won't see the cap).
- [ ] Observe PR #83 prompt output on a fresh cushlabs.ai crawl — confirm quick wins are diversified and strategic recs are specific.
- [ ] Rotate the `SENTRY_AUTH_TOKEN` (exposed in chat 2026-06-28).

### Technical Debt

- Pre-existing `tsc` error in `CrawlDetailPage.tsx` (sort-direction comparison) — not blocking the Vite build, but should be cleaned up.
- Caddyfile CSP edits live only on the VPS, not version-controlled.

### Open Questions / Blockers

- None.

---

## Session: 2026-06-29

### Accomplished

- Fixed Sentry error `BACKEND-...-6`: ported `010_audit_logs.sql` (adds `audit_log.ip_address`) into the CLI migration set and applied via `supabase db push` (PR #78).
- Image thumbnails now render: relaxed scraper CSP `img-src` to allow `https:` (VPS Caddyfile).
- Wrote `docs/FEATURES.md` + added Features & Benefits section to Use Cases page (PR #76); deep-linked landing persona cards to use-case anchors (PR #77).
- Landing page: replaced 3-step "How It Works" with 5-step stepper + added "Surfacing the signals that matter" severity section (PR #79).
- Portfolio: optimized cover thumbnail + 8 marketing slides (cropped NotebookLM watermark) + brief video (29MB→14MB) to WebP/H.264; corrected PORTFOLIO.md (live_url, asyncio not Celery, health flags); EN+es-MX alt text (PR #79, #80).
- Published ai-webscraper portfolio: uploaded 11 assets to R2 CDN, regenerated cushlabs `projects.generated.json`, deployed — live at www.cushlabs.ai/projects/ai-webscraper/ (cushlabs PR #138).
- Added "hidden from Google" (noindex) issue check — zero added cost, plain-English (PR #81).
- AI report: reworked Executive tab to lead with the treatment plan (critical issues, quick wins w/ copy buttons, strategic recs w/ impact×effort); fixed word-count bug (was page bytes); this also un-broke thin-content detection which never fired (PR #82).

### Decisions Made

- Indexing checks: added only noindex (high-value, plain-English); skipped canonical/robots/sitemap as too technical for the owner audience.
- "Copy-paste fixes" wording: hybrid ("paste into CMS or hand to your AI assistant") — accurate without narrowing the audience.
- Portfolio assets served from Cloudflare R2 CDN via `upload-to-r2.ts`, not committed to cushlabs/public.

### Immediate Next Steps

- [ ] Re-run a crawl to verify the word-count fix end-to-end (existing crawls have NULL `word_count` until re-run).
- [ ] Rotate the `SENTRY_AUTH_TOKEN` (exposed in chat 2026-06-28).
- [ ] (Optional) Score differentiation so perfect-score reports feel earned, not generic.

### Technical Debt

- Word-count correct only on new crawls; existing crawls need a re-run.
- Caddyfile CSP edits (vitals + img-src) live only on the VPS, not version-controlled.
- Old DB password remains in git history (rotation deferred).

### Open Questions / Blockers

- None.

---

## Session: 2026-06-28

### Accomplished

- Diagnosed production outage: Supabase project `cushlabs-site-analysis` was auto-paused (INACTIVE) → DB unreachable for frontend (auth) and backend; restored by Robert.
- Fixed CSP on VPS Caddyfile — added `https://vitals.cushlabs.ai` to scraper `connect-src`, validated + reloaded Caddy (verified live).
- Added GitHub Actions Supabase keep-alive cron (`.github/workflows/keepalive.yml`, PR #63) — decoupled from VPS, pings PostgREST every 2 days.
- Security sweep: 75 → 3 Dependabot alerts, **0 critical / 0 high**. Backend PR #64 (Pillow 10.1→12.2 critical, python-multipart→0.0.31, python-dotenv→1.2.2). Frontend PR #65 (axios→1.18.1, react-router→6.30.4 + `overrides` for nth-check/postcss/serialize-javascript/webpack-dev-server/bfj/underscore). Merged CI bump #62; closed 20 superseded Dependabot PRs.
- Deployed both: backend via `docker compose pull` from GHCR (box pulls `:latest`, never builds locally — `--build` is a no-op), frontend via `scp build/*`. Verified live versions + health 200.
- Removed DB password from `.claude/settings.local.json` and untracked it (gitignored).
- **Migrated frontend Create React App → Vite 8 + Vitest 4 (PR #66)** — eliminated the 30 residual build-time npm advisories at the root. npm tree ~1450→274 packages, `npm audit` 0 vulnerabilities. Converted `process.env.REACT_APP_*`→`import.meta.env.*`, jest→vitest (35/35 tests pass), postcss/tailwind configs→`.cjs`, `public/index.html`→root. Deployed + verified live (root/asset/SPA-route all 200, Supabase + prod API URL baked into bundle).

### Decisions Made

- Keep-alive via GitHub Actions, not in-process: the existing 10-min stale-crawl monitor already warms the DB while the backend is up; the project only paused during backend downtime, so the fix must be VPS-decoupled.
- Eliminated the 30 residual build-time npm alerts by migrating off `react-scripts` (CRA) to Vite, rather than band-aiding with `overrides` — Vite has a tiny modern tree and supports the planned voice-agent SDKs better than CRA's webpack.
- Skipped trafilatura 1.7→2.0 (PR #42 left open): breaking major, in active use (content_extractor), no advisory.

### Immediate Next Steps

- [ ] Add repo Actions values for keep-alive cron: `SUPABASE_URL` + `SUPABASE_ANON_KEY` (cron fails fast until set).
- [ ] Rotate the `SENTRY_AUTH_TOKEN` (exposed in chat this session).
- [ ] Update CLAUDE.md stack description: "React 18 + Create React App" → Vite (left out of PR #66 to avoid conflicting with unrelated uncommitted CLAUDE.md edits).

### Technical Debt

- Old DB password remains in git history (untracked going forward; rotation deferred per Robert — no activity/exposure).
- Main Vite chunk >500 kB (single `index` bundle) — fine for now; could route-level code-split later.

### Open Questions / Blockers

- None.

---

<!-- New entries go above this line -->
