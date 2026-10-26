# Session Log — ai-webscraper

Entries are newest-first. Each entry documents one Claude Code working session.

---

## Session: 2026-10-26 (backend container runs as non-root; PR #116)

**Outcome:** PR #116 merged and deployed. The backend container runs as uid 1000 instead of root; the
storage volume is owned by that user.

### Accomplished

- **Non-root container.** `backend/Dockerfile` creates an `app` user (uid 1000) and switches to it.
  The only runtime write path is `STORAGE_DIR` (/app/storage), the `webscraper-storage` volume in
  production. That volume was chowned to uid 1000 on the box immediately before the recreate, and
  the Dockerfile documents the one-line chown a fresh host needs. For a plain `docker run` without a
  volume the image pre-creates `/app/storage` owned by the app user.
- **Deployed** via `cushlabs-prod-server/scripts/deploy-service.sh webscraper` (auto-rollback on
  failed healthcheck). Live: `uid=1000`, healthy, https://scraper.cushlabs.ai/api/v1/health/ reports
  version `012f96e` and environment `production`, storage writable, no permission errors in the log.
  The compose service also carries `no-new-privileges` and `cap_drop: ALL` since prod-server PR #30.

### Immediate Next Steps

- [ ] None from this session. `scripts/smoke-prod.sh` will report drift until the next backend merge
      only if the SHA check is strict; the health endpoint already shows the merged SHA.

---

## Session: 2026-10-20 (afternoon: messaging review made honest; PR #114)

### Accomplished

- **Robert's CushLabs assistant reviewed the Content & Brand tab and found it generic**: six unlike pages with the identical 75/80/70 sub-scores, advice to add a value proposition and CTA already on the page, Title Case heading rewrites on a sentence-case site, a suggested meta that dropped the MXN price, no quoted copy anywhere. Verified in code: gpt-4o-mini, 600 output tokens, fed a skeleton (H1, up to 10 H2s, first sentence of 8 paragraphs, button labels, URL-guessed purpose), no rubric, no evidence field, and a prompt whose own rules ("do not penalise absence of urgency", "cite actual copy") the model ignored. The scores were not a code fallback; each page's prose was distinct.
- **Decision (operating vision applied):** small fix, not a rebuild. The tab had no revenue hypothesis and was a credibility leak in a client-facing report; removing wrong numbers protects what pays, a rubric rebuild would not provably differentiate. Robert: "small fix".
- **PR #114:** scores stripped before storage and from the UI; `strategy_evidence.py` evidence gate (model must quote verbatim; Python verifies against the skeleton; unverified pages lose gaps/issues/suggestions/recommendation and show "no verifiable note"); tab relabelled "Messaging Review, AI reading, not a score" with the quoted lines shown above each note; prompt forbids recommending what is already present, changing heading case, adding urgency, dropping currency/market; `pricing` is its own page purpose; executive narrative gets recommendations with their quote and no scores; health score content pillar no longer blends a strategy score.
- Tests: backend 231 (6 new), frontend 55, tsc + build clean. Deployed both tiers; report regenerated on the verification crawl from the server to confirm the gate: scores gone, 2 of 10 pages dropped for invented quotes.
- **PR #115:** the regenerated About page's only note was to replace its "Toggle theme" button, because the skeleton builder listed every `<button>` as a CTA. Site chrome (theme, menu, cookie consent, search, carousels, dialogs, aria-expanded/haspopup) is now excluded. Regenerated again: 9 of 10 pages carry verified quotes. Honest limit, unchanged: the surviving advice is still generic in places (a page is told to add a CTA while quoting its own "Start Your Free Trial" button); the gate makes it checkable, not smart. That is the rebuild Robert declined, by design.

### Decisions Made

- A content-strategy number returns only if computed from counted signals with a published rubric (recorded in CLAUDE.md).
- Descriptive prose (detected tone, assessment) is kept but hidden in the UI when a page has no verified quote.

### Immediate Next Steps

- [ ] Upstash limiter still failing open (unchanged): https://console.upstash.com/redis usage check.

### Technical Debt

- `batches.py` references a non-existent `batch.rate_limit` (dead route).
- Prod smoke test performs no write.

---

## Session: 2026-10-20 (performance findings were wrong: PageSpeed Insights + honest TTFB; PR #113)

### Accomplished

- **Robert challenged the report's performance findings** (seven cushlabs.ai pages "slow"/"critical", up to 3,788 ms) against a Lighthouse run in the high 90s. Investigation: the only stored number was one whole-fetch reading per page from the Ashburn VPS, taken through the apex->www redirect (relative links were resolved against the pre-redirect URL, so every discovered page inherited the hop), while our own link checker was hitting the host (first three pages, before probing began: 532-941 ms; every page after: 1.2-3.8 s). Re-measured from Guadalajara: 0.23-0.40 s for every page; from the VPS: typically 0.24-0.43 s with occasional 1-2 s spikes on the Cloudflare->Vercel path.
- **PR #113 (merged, deployed):**
  - `services/pagespeed.py`: Google PageSpeed Insights (Lighthouse) for the start page (mobile + desktop, started alongside the crawl) and up to 3 primary pages (after it). Stored on `crawls.pagespeed`; `PageSpeedCard.tsx` on the Executive tab; PDF section; AI narrative told it is the performance authority; a finding only below Lighthouse's 90. Key restricted to `pagespeedonline.googleapis.com` created with gcloud and written straight to the VPS env (never in chat); keyless fallback kept.
  - `core/performance.py`: Google's TTFB bands (pass < 800 ms, slow < 1800 ms, poor above) on a **median of samples**; severity capped at medium; wording names the measurement and its origin ("measured from our US-East server"). "critical" is gone.
  - Crawler: `_timed_get` splits redirect / TTFB / download; `_resample_response_times` takes two more TTFB samples per page after the crawl with the link checker idle (cap 25 pages, stops on 429/503); apex and www are one site; the start URL's redirect target becomes internal; links resolve against `final_url`; a redirecting start URL is one low finding, redirecting internal targets one aggregated finding.
  - Migration `20261020160000`: `pages.final_url/ttfb_ms/redirect_ms/ttfb_samples`, `crawls.pagespeed` (applied before deploy, additive).
  - Exports renamed "Speed" -> "Server Response" with the ms value; `summary_stats.performance_metric/target/pagespeed_mobile_score`.
- Tests: backend 225 (22 new), frontend 55 (2 new).
- Confirmed for Robert that user-facing error text is already fixed (PR #112): one calm sentence + reference code to the person, full error in the console/Network tab, cause in the server log under the same code.

### Decisions Made

- Lighthouse is quoted for "performance"; our own fetch timing is labelled server response time and never carries more than medium severity. A one-location server reading is a hint.
- Change the measurement, not the thresholds alone: median of three against the final URL, redirects timed separately.
- PageSpeed runs for every tier (free, 5 calls per crawl against a 25k/day quota).

### Immediate Next Steps

- [ ] Verification crawl of https://www.cushlabs.ai on the box (service client + worker) after deploy; report regenerated by Robert from the UI.
- [ ] Upstash limiter still failing open (unchanged): https://console.upstash.com/redis usage check.

### Technical Debt

- `batches.py` still references a non-existent `batch.rate_limit` (dead route).
- The prod smoke test still performs no write; a create-and-delete crawl probe would catch schema drift within hours.

---

## Session: 2026-10-20 (crawl creation broken since PR #110: INTEGER column vs float; 5xx contract)

### Accomplished

- **Root cause of the broken crawl creation found and fixed in production.** With the 422 handler deployed, Robert's retry produced a 500 whose toast read the raw Postgres dict: `invalid input syntax for type integer: "1.0"` (22P02). PR #110 restored `float(rate_limit)` in `create_crawl` (the `int()` cast from 0864680 had turned 0.5 req/s into 0 and the limiter divided by zero), but `crawls.rate_limit` was created as `INTEGER` in `20251216000359_init_schema.sql`. So every crawl creation since the politeness release failed at the insert. Not caught by tests because the DB is mocked; not caught by the smoke test because it never creates a crawl.
- **Migration `20261020030000_rate_limit_numeric.sql`** widens `crawls.rate_limit` and `batches.rate_limit` to `NUMERIC(5,2)`. Applied with `supabase db push` (column type read before/after via the PostgREST OpenAPI from inside the container: integer -> numeric), then verified with a throwaway insert of 1.0 and 0.5 under Robert's user id, deleted in the same script. Crawl creation worked in production again before the PR was even opened.
- **5xx contract** (`app/core/errors.py`, PR #112): every `HTTPException` >= 500 and every uncaught exception now returns `{"detail": "Something went wrong on our side. ...", "error_id": "<8 hex>"}`; the cause is logged as `Server error <id> on POST /path: ...`. Status code and headers preserved; 4xx sentences untouched. The request-logging middleware's catch-all returns the same shape. ~45 route-level `detail=f"...{e}"` strings are now log-only.
- **SPA**: `apiError.ts` ignores any 5xx body except `error_id` ("Reference: ..."); the axios client retries only GET/HEAD/OPTIONS (it had re-sent the failing crawl POST three times; a POST that reached the server may already have created the crawl and used a free-tier slot).
- Tests: backend 206 (3 new), frontend 53 (2 new), tsc + build clean.

### Decisions Made

- Change the column, not the code: the form (step 0.1), the Pydantic model (float, ge=0.1) and the crawler's limiter all want fractions; the INTEGER column was the one outlier, and the two code-side "fixes" each broke production in turn.
- A 5xx never carries words from a driver, Postgres or an upstream API. The reference id replaces them for the user; the log keeps the cause.
- Retries are restricted by method, not removed: GET retries still smooth over transient 502s during a container restart.

### Immediate Next Steps

- [ ] Robert's own confirmation of a crawl created from the form (the only step that cannot be run from here: it needs his browser session). Server-side proof already exists.
- [ ] Upstash still reports "temporarily rate-limited" on every mutating request, so the API limiter fails open. Check usage at https://console.upstash.com/redis and give this app its own database if the free quota is shared.

### Technical Debt

- Still open: the original 422s at 01:09 UTC never reproduced (the same payload passes validation now); the handler from #111 will name the field if it recurs.
- The prod smoke test never exercises a write. A create-and-delete crawl probe with a service token would have caught this class of failure within hours instead of at Robert's next click.
- `batches.py` references `batch.rate_limit` on a model that has no such field (batch creation is dead code).

---

## Session: 2026-10-19 (evening: unexplained 422 on crawl creation; error contract, dependency lock, CSP fix)

### Accomplished

- **PR #111 merged and deployed (2e5025b), smoke green on both tiers.** Robert's first crawl of www.cushlabs.ai after the politeness release was refused with a 422 and the toast read axios's "Request failed with status code 422". He called it out as unacceptable for a user-facing product; the fix makes that class of failure impossible to hide again.
- **Root-cause investigation (still open at close):** the production log proved the route body never ran, so the 422 is FastAPI request validation, not the new user-agent check. The exact form payload returns 200 through TestClient, through a real uvicorn with production's package set rebuilt locally, and inside the live container on the VPS. The cause therefore lives in the live request itself; after this deploy the next rejection names its field in both the toast and `docker logs webscraper` ("Validation rejected POST /api/v1/crawls/: field: reason").
- **Error contract** (`backend/app/core/errors.py`): RequestValidationError handler logs field + reason (never the value) and returns `{"detail": [{loc,msg,type}], "message": "field: reason"}`. The default body used to echo `input` back to the client.
- **Frontend** (`src/lib/apiError.ts`): `getApiErrorMessage(err, fallback, labels)` renders 422 lists with form labels, string/structured details, 429/5xx/network cases; never an axios message or status code. Wired into CrawlNewPage, CrawlDetailPage, ReportPanel. The crawl form trims URL/name/user agent before sending.
- **Dependency lock** (`backend/constraints.txt`, `-c constraints.txt` in Dockerfile and CI, `scripts/lock-backend-deps.sh`): the image built this afternoon had resolved 45 packages newer than any dev machine (starlette 0.52 -> 1.9, anyio, h11, httpx, openai 1.109 vs local 2.26 ...). Pinned to the set the suite and production ran on.
- **CSP fix, live on the VPS:** the Caddyfile's `connect-src` omitted `https://vitals.cushlabs.ai`, so every Web Vitals report had been blocked by the browser since the tracker was added. Added with backup (`/etc/caddy/Caddyfile.bak-20261019-csp`), `caddy validate`, reload. `scripts/smoke-prod.sh` now fails if it regresses.
- **Test hygiene:** `tests/conftest.py` resets the in-memory rate limiter per test; the suite's cumulative POSTs (one identity, `ip:testclient`) had started to 429 later tests once more route tests were added.
- **Deploy script:** `scripts/deploy-backend.sh` now accepts a short SHA and polls up to 3 minutes for the image-build run instead of aborting on the first miss (both bit this evening).
- Tests: backend 203 green (12 new), frontend tsc + 51 vitest (11 new) + build.

### Decisions Made

- Keep FastAPI's `detail` list shape (minus `input`/`ctx`/`url`) and add a top-level `message`; field labels are applied client-side where the form knows them.
- Pin via a constraints file rather than fully pinning requirements.txt: direct deps and their floors stay readable, Dependabot keeps bumping them, and the lock is regenerated inside python:3.12-slim so Linux-only markers match the image.
- Reverted prettier's whole-file reformat of CrawlDetailPage.tsx and ReportPanel.tsx (2,000+ cosmetic lines) and applied only the three real edits.

### Immediate Next Steps

- [ ] Robert retries the crawl (Start URL `https://www.cushlabs.ai`, defaults). Read `docker logs webscraper | grep "Validation rejected"` for the field, then fix the actual cause.
- [ ] Upstash reports "Your database has been temporarily rate-limited" on every mutating request, so the API limiter is failing open (by design). Check the Upstash console usage for the shared database; if another project is consuming the free quota, give this app its own database.

### Technical Debt

- `_is_private_ip` SSRF checks still only cover sitemap URLs (carried over).
- `openai` in production is 1.109.1 while local dev has 2.26.0; the constraints file now freezes production at 1.109.1. Any move to the 2.x SDK is a deliberate bump in requirements.txt + regenerated lock.

### Open Questions / Blockers

- The live request's 422 reason: unknown until the next submission lands with the new handler deployed.

---

## Session: 2026-10-19 (crawler politeness: robots.txt, backoff, honest bot identity; Google sign-in restored)

### Accomplished

- **PR #110 merged and deployed (026a922), smoke green on both tiers.** Robert asked whether the crawler avoids getting the VPS IP blocked; the review found it did not, and he asked for the fixes at no added cost (no proxy, no extra paid API).
- **New `app/services/politeness.py`**, wired into the crawler at the single chokepoint in `Crawler._crawl()`: robots.txt `Disallow` + `Crawl-delay` (floor on the request interval, capped 30s) + `Sitemap`, one fetch per host, fail-open on 4xx/5xx/error. The old "respect robots.txt" option only read Sitemap lines. Free users can no longer switch it off; admins may for sites they own.
- **Backoff**: 429, 503 and CDN challenge pages (Cloudflare `cf-mitigated`, "Just a moment", Incapsula, PerimeterX, DataDome, Akamai markers) penalise the HOST bucket with Retry-After or exponential delay, retry a URL at most twice, stop the crawl after 3 consecutive blocks; reason lands in `crawls.error` (detail page already renders it as an amber banner). A plain 403 is still recorded as a page.
- **Per-host pacing shared across crawls** (`politeness.host_buckets`); `RateLimiter` re-exported from `crawler.py` so the old tests still pass; 0 req/s no longer divides by zero (the route was also storing `rate_limit` as int, so 0.5 became 0).
- **Link probes**: one HEAD per unique normalised URL per crawl, capped at 200; skipped for robots-disallowed URLs and once the site has pushed back.
- **Identity**: `CushLabsBot/1.0 (+https://scraper.cushlabs.ai/bot.html)`; browser-impersonating agents refused with 422; the fake Chrome string in config and the example.com placeholder are gone. `frontend/public/bot.html` explains the bot and how to block it; `scripts/smoke-prod.sh` checks it.
- **Route fix**: `create_crawl`'s catch-all was turning every `HTTPException` (the free-tier 403, the new 422) into a 500. Now re-raised.
- **Tests**: 54 new in `tests/test_politeness.py` (unit + crawler integration with real `httpx.Response` objects + the route through TestClient with dependency overrides). Backend 191 green; frontend tsc / vitest 35 / build green.
- **Google sign-in restored** (no repo change): `deleted_client` was the GCP OAuth client being gone; Robert created a new Web client in `cushlabs-1774756152745`, first attempt hit `redirect_uri_mismatch` (callback URI mistyped), fixed. Verified from the outside that Supabase sends `https://kbltwyiowkbxzhhhozxf.supabase.co/auth/v1/callback` and a client id from project number 459730729117 by reading the `/auth/v1/authorize?provider=google` redirect without following it.

### Decisions Made

- Robots enforcement happens at queue-pop time, not at link-discovery time, so sitemap entries, nav-detected links and external hosts all go through one gate.
- 503 counts as push-back even without challenge markers: an overloaded origin and a WAF both want us to slow down.
- Crawl-delay is capped at 30s so a 50-page crawl still finishes inside the 1h runtime; the user's rate limit can only slow, never speed past it.
- `_should_crawl_url` was NOT added to the chokepoint: its extension filter would drop PDFs discovered via links, which the product records on purpose.

### Immediate Next Steps

- [ ] First production crawl of a site with a real `Crawl-delay` or a 429 is the only path not exercised live (the agent has no user account); look for "backing off" / "robots.txt disallows" in `docker logs webscraper` after Robert's next crawl.

### Technical Debt

- The VPS IP is still a datacenter address with no proxy; CDN bot management that challenges datacenter ranges regardless of politeness is a cost decision (Firecrawl for more pages, or a residential proxy), explicitly deferred by Robert.
- `_is_private_ip` SSRF checks run only for sitemap URLs, not for links discovered on pages. Pre-existing; noted during this review, left for a focused change.
- GitHub Actions was in "degraded performance" during this session; the CI run showed as queued for 25+ minutes while the jobs had actually finished in under a minute. Trust `gh api .../jobs` over `gh pr checks` when that happens.

### Open Questions / Blockers

- None.

---

## Session: 2026-10-19 (Dependabot sweep: PyJWT, React Router 7)

### Accomplished

- **PR #109 merged and deployed (092d11e), smoke green on both tiers.** Zero open Dependabot alerts afterwards (was critical 1 / high 1 / medium 3).
- **python-jose -> PyJWT** in `core/auth.py` and `middleware/rate_limiter.py`. ES256/RS256 allowlist, JWKS lookup and the unknown-kid Supabase fallback preserved. New `tests/test_auth_jwt.py` (12 specs): valid ES256 accepted; HS256 forged with the server public key, tampered payload, expired, missing kid, wrong key all refused; unknown kid -> fallback; limiter sub bucketing. Suite is 137 green. Verified PyJWK builds an `ECPublicKey` from the LIVE Supabase JWKS entry (ES256).
- **React Router 6.30.6 -> 7.18.4.** App already ran with the v7 future flags; only change was removing the `future` prop. Playwright: client-side nav, protected-route redirect and 404 all fine.
- **postcss-selector-parser** forced to 7.1.6 via npm `overrides` under Tailwind 3 (build + tests green).
- **braces** (high, no patched version, dev-only via tailwind 3 file watching) dismissed on GitHub as tolerable risk with a dated comment; revisit on Tailwind 4.

### Decisions Made

- Keep the asymmetric allowlist as the primary defence regardless of library; the PyJWT swap removes the unmaintained dependency rather than relying on its guard.
- Dismiss rather than chase `braces`: nothing to upgrade to, never reaches the browser.

### Immediate Next Steps

- [x] **Live login verified:** GitHub sign-in worked for Robert after the deploy, so the PyJWT path is confirmed in production.
- [ ] **Google sign-in is broken at Google, not here:** `Error 401: deleted_client` ("The OAuth client was deleted"). The dedicated "AI WebScraper" GCP project from the archived setup guide no longer exists (not among the 7 active projects; the 2026-08-27 cleanup's 30-day undo expired 2026-09-26). Fix is a new Web OAuth client in `cushlabs-1774756152745` with redirect `https://kbltwyiowkbxzhhhozxf.supabase.co/auth/v1/callback`, then Client ID + client secret into Supabase Auth -> Providers -> Google. Dashboard-only: no gcloud/API exists for creating OAuth clients, and the Supabase CLI's management token is not stored where a script can use it on this machine.
- [ ] First real login after this deploy is the only path not exercised locally (the agent has no user account to sign in with); if a 401 appears, look for "JWT verification failed" in `docker logs webscraper` to see the cause.

### Technical Debt

- Tailwind 3 pins the braces/micromatch/chokidar chain; a Tailwind 4 migration clears it (read ~/.claude/reference/tailwind-4-migration.md first).

### Open Questions / Blockers

- None.

---

## Session: 2026-10-18 (production hardening, test gates, brand alignment)

### Accomplished

- **Deployed and verified:** b900aac live on both tiers; `scripts/deploy-backend.sh` + `deploy-frontend.sh` both ended in a passing smoke, the manual `production-smoke.yml` run passed, image is 577 MB on the box (was 4.13 GB), container 126 MB RSS.
- **Audited the live system first.** scraper.cushlabs.ai healthy (container up 3 months, 0 restarts, no errors in 48h of logs, 145 MB RSS), production matched `main`, Sentry + Upstash rate limiting wired. The gaps were in the harness and the hygiene, not the runtime.
- **Pre-publish gate fixed:** CI never ran the 35 Vitest specs (type-check + build only). Added `npm test` to the frontend job and `backend/tests/test_api_smoke.py` (14 specs that boot the real app with TestClient: health payload, security headers, HSTS gating, 413 body cap, anonymous refusal on five endpoints, bad bearer -> 401, CORS allow/deny). Suite is 125 green.
- **Post-publish gate added:** `scripts/smoke-prod.sh` (health + version, hardening headers, auth gate, frontend CSP + bundle + `app-version` meta, drift vs `main`). Runs twice daily from `.github/workflows/production-smoke.yml` (drift = warning) and at the end of both new deploy scripts (`scripts/deploy-backend.sh`, `scripts/deploy-frontend.sh`; drift = failure).
- **Version stamping:** Dockerfile `ARG GIT_SHA` -> `APP_VERSION`, reported by `/api/v1/health/`; CI passes `github.sha`. Frontend stamps `VITE_APP_VERSION` into `<meta name="app-version">`.
- **Image went from 4.13 GB Playwright base to python:3.12-slim + curl.** Nothing in `app/` imported Playwright/Selenium (JS rendering is Firecrawl since c66fccf); `crawler_backup.py`, the dead `app/api/api_v1` + `app/scrapers` packages, and `selenium`/`webdriver-manager`/`playwright`/`asyncpg`/`passlib`/`validators` requirements removed. curl kept because the compose healthcheck shells to it.
- **Backend deps:** FastAPI 0.104.1 (Oct 2023) -> 0.146.0, uvicorn 0.54, pydantic-settings 2.16, Pillow >=12.3.0 (clears 12 Dependabot advisories). Pydantic `class Config` -> `ConfigDict` (15 models), `Query(regex=)` -> `pattern=`. Booted the real app against the local config to confirm.
- **Frontend deps:** axios 1.20, react-router-dom 6.30.6, transitive bumps via `npx npm@latest update` (bundled npm 10.9.9 crashes with `edgesOut` on full installs; memory note saved). Audit 19 -> 10; the rest are Tailwind 3's dev-watcher chain and React Router 7 (major).
- **Brand kit alignment** (operating-system/cushlabs/brand-kit.md): accent `#FF6A3D` (hover `#FD4C00`), neutral grey scale replaces slate, shadcn `--primary`/`--ring` off the default blue, Manrope + Inter self-hosted (`public/fonts`, same files as cushlabs.ai; Inter was never actually loaded before), chevron mark in header/footer/favicon/apple-touch/OG image (rendered via Playwright), teal removed, public pages (home, docs, use cases, search, modal) moved to the single accent, muddy orange-to-grey hero gradient replaced. Verified with Playwright screenshots + computed-style checks.
- **Hygiene:** deleted `railway.json`, `render.yaml`, `frontend/vercel.json`, `.windsurf/`, three stray `=0.7.0`-style pip artifacts, six loose backend scripts, 18 one-off migration/RLS scripts (incl. `completely_disable_users_rls.py`, `get_db_password.py`) from a public repo; archived four Render-era guides to `docs/archive/`. README, CLAUDE.md, PORTFOLIO.md, scripts/README, frontend BRAND.md rewritten for the real stack (Vite, no Celery, Hetzner).

### Decisions Made

- One bundled PR per Robert's request; this app deploys to Hetzner via GHCR, so Vercel limits do not apply.
- Swapped the values under the historical `primary`/`secondary` names rather than renaming 480 class references; `primary-*` = neutrals, `secondary-*` = accent (documented in CLAUDE.md and BRAND.md).
- Drift is a warning on the schedule (VPS pull is deliberately manual) but a failure inside the deploy scripts.
- Authenticated-app report tabs keep blue/purple category colors for now; a visual-semantics change inside the report deserves its own pass.

### Immediate Next Steps

- [ ] Replace python-jose with PyJWT. After the merge Dependabot raised a CRITICAL with no patched version (python-jose <= 3.5.0, algorithm-confusion guard bypass via DER public keys). Verified not reachable here: the only `jwt.decode` in `core/auth.py` pins `algorithms=["ES256", "RS256"]` (no HMAC), and the kid-miss fallback validates server-side via `supabase_client.auth.get_user`. Still an unpatched critical on a public repo; swap the library in its own PR with the API smoke tests as the gate.
- [ ] Decide on React Router 7 (remaining runtime advisory, major upgrade).
- [ ] Report tabs / CrawlDetail / Dashboard still use blue + purple as category colors; single-accent pass if the kit's rule is meant to reach inside the app.
- [ ] Rotate or remove the dead Sentry org auth credential in local env files (carried over from 2026-07-06).

### Technical Debt

- `backend/CLAUDE_BACKEND.md` and `frontend/CLAUDE_FRONTEND.md` were not re-audited this session.
- Caddy CSP still lives only on the VPS.

### Open Questions / Blockers

- None.

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
