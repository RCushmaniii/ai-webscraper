# Session Log — ai-webscraper

Entries are newest-first. Each entry documents one Claude Code working session.

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
