# Session Log — ai-webscraper

Entries are newest-first. Each entry documents one Claude Code working session.

---

## Session: 2026-06-30

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
