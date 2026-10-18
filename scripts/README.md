# Scripts

Operational scripts for AI WebScraper. Shell scripts are **bash** (run from Git Bash on Windows, or via Claude's Bash tool); they are not PowerShell.

## Deploy & verify

| Script | What it does |
|--------|--------------|
| `deploy-backend.sh [sha]` | Waits for the GHCR image build of `main` (or `sha`), pulls + recreates the `webscraper` container on the Hetzner VPS, waits for container health, prunes old image layers, then runs the smoke test expecting that SHA. |
| `deploy-frontend.sh` | Vite-builds the frontend with `VITE_APP_VERSION=<HEAD sha>`, copies it to the Caddy static root on the VPS, then runs the smoke test expecting that SHA. |
| `smoke-prod.sh [base-url]` | Production smoke test: API health + version, security headers, auth gate, frontend CSP + bundle, app-version meta, and version drift against `EXPECTED_VERSION`. Also run twice daily by `.github/workflows/production-smoke.yml`. |

```bash
bash scripts/deploy-backend.sh
```

```bash
bash scripts/deploy-frontend.sh
```

```bash
bash scripts/smoke-prod.sh https://scraper.cushlabs.ai
```

## Diagnostics (Python, read-only against Supabase)

| Script | What it does |
|--------|--------------|
| `check_table_schema.py` | Print the live column list of a table — the field-name gotchas in CLAUDE.md come from here. |
| `check_latest_crawl.py` | Show the most recent crawl row and its page counts. |
| `monitor_crawl.py` | Poll a running crawl's progress. |

Run from the repo root with the backend `.env` present:

```powershell
python scripts/check_table_schema.py
```

## Local dev

| Script | What it does |
|--------|--------------|
| `dev-wt.bat` | Start backend + frontend in Windows Terminal tabs. |

`start.bat` in the repo root is the plain-console equivalent.

## History

Migration-runner and RLS one-off scripts that used to live here were removed on 2026-10-18. Schema changes go through `supabase db push` (`supabase/migrations/`); the old scripts are in git history if ever needed.
