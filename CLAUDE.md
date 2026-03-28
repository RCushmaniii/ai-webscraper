# AI Web Scraper - Claude Context Guide

> **Purpose**: This document provides context for AI assistants (like Claude) working on this codebase. It documents conventions, patterns, and critical knowledge to maintain consistency and quality.

---

## Project Overview

**AI Web Scraper by CushLabs** is a web crawling and site analysis platform with tiered access.

### Core Mission

- Crawl websites starting from a URL
- Extract and store page content for inspection
- Detect high-signal SEO and technical issues
- Generate AI-powered analysis reports
- Provide tier-based access (Free: 3 crawls / 50 pages max, Admin: unlimited)

### Explicit Non-Goals (v1)

- ❌ Selector-based scraping
- ❌ Real-time dashboards with WebSockets
- ❌ Payment/billing integration (planned for v2)

---

## Technology Stack

### Frontend

- **Framework**: React 18 + Create React App
- **Language**: TypeScript
- **Styling**: TailwindCSS + shadcn/ui components
- **Routing**: React Router v6
- **State**: React Context API (AuthContext)
- **Auth**: Supabase Auth with JWT tokens

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **Server**: Uvicorn ASGI server
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth + Row Level Security (RLS)
- **Background Tasks**: FastAPI BackgroundTasks (in-process, no external dependencies)
- **Scraping**: BeautifulSoup4, Playwright (JS rendering)

---

## Claude's Execution Authority

> **IMPORTANT**: Claude has full authority to execute tasks directly. Do NOT assign work back to the user.

### Supabase CLI Access

- **Supabase CLI is ENABLED** and available in this environment
- Claude has **direct database access** via the CLI
- Execute migrations, queries, and schema changes directly
- No need to tell the user "run this in Supabase dashboard" - just run it

### Empowerment Principles

1. **Execute, don't delegate** - Run commands and migrations directly
2. **Fix issues immediately** - Don't list steps for the user to follow
3. **Use available tools** - Supabase CLI, bash, file editing - all are available
4. **Complete the work** - The goal is a working solution, not instructions

### Available Supabase CLI Commands

```bash
# Run SQL migrations directly
supabase db push                    # Push local migrations to remote
supabase db reset                   # Reset database (careful!)
supabase migration new <name>       # Create new migration file

# Query and inspect
supabase db lint                    # Check for issues (like RLS performance)
supabase inspect db                 # Database inspection tools

# Other useful commands
supabase status                     # Check connection status
supabase projects list              # List linked projects
```

### When Claude Should Act Directly

- Database migrations - **execute them**
- Schema changes - **run the SQL**
- Bug fixes - **make the changes**
- Performance fixes - **implement and apply**
- Linter warnings (like RLS issues) - **fix and deploy**

### The Only Exceptions (ask first)

- Destructive operations that cannot be undone (DROP DATABASE, etc.)
- Changes that affect production auth/billing
- Anything the user explicitly wants to review first

---

## Architecture Principles

### 1. Security First

- **Row Level Security (RLS)** on ALL database tables
- **Admin-only access** - manual user provisioning required
- **Server-side validation** for all mutations
- **No client-side security assumptions**

### 2. Database Field Naming

**CRITICAL**: Always verify actual database column names before writing code.

Common gotchas:

- ✅ `completed_at` (correct) vs ❌ `finished_at` (wrong)
- ✅ `follow_external_links` (correct) vs ❌ `follow_external` (wrong)
- ✅ Always query the database schema to confirm

### 3. Performance Optimization

- **Batch database operations** wherever possible
- Example: Save 100 links in ONE call, not 100 separate calls
- **Reduce logging verbosity** for noisy libraries (httpx, httpcore)
- **Use background tasks** (Celery) for long-running operations

### 4. Code Organization

- **Separation of concerns** - routes, services, models clearly separated
- **DRY principle** - extract common patterns into reusable functions
- **Type safety** - use Pydantic models for validation
- **Error handling** - graceful degradation with informative messages

---

## Common Patterns

### Backend: Database Operations

**Bad** (Individual inserts):

```python
for link in links:
    db.table("links").insert(link).execute()  # 100 DB calls!
```

**Good** (Batch insert):

```python
db.table("links").insert(links).execute()  # 1 DB call!
```

### Backend: Field Name Consistency

**Always check database schema first**:

```python
# Query actual schema
client.table("crawls").select("completed_at, created_at").limit(1).execute()

# Then use correct field names in code
update_data = {
    "status": "completed",
    "completed_at": datetime.now().isoformat(),  # Matches DB!
    "updated_at": datetime.now().isoformat()
}
```

### Frontend: Case Sensitivity

**File names MUST match imports exactly**:

```typescript
// ✅ Correct
import SignUpPage from "./pages/SignUpPage"; // File: SignUpPage.tsx

// ❌ Wrong
import SignupPage from "./pages/Signuppage"; // Will fail!
```

### Frontend: Protected Routes

All authenticated routes use the `ProtectedRoute` wrapper:

```typescript
<Route path="crawls" element={<ProtectedRoute element={<CrawlsPage />} />} />
<Route path="users" element={<ProtectedRoute element={<UsersPage />} adminOnly={true} />} />
```

---

## Critical Knowledge

### 1. External Link Safety Features

**Database Table**: `crawls`

- `follow_external_links` (boolean) - Whether to follow external domains
- `max_external_links` (integer) - Limit external domains (default: 5)
- `external_depth` (integer) - How deep to crawl external sites (default: 1)

**Domain Blacklist**: `backend/app/core/domain_blacklist.py`

- Prevents crawling social media (Facebook, Twitter, etc.)
- Blocks analytics/tracking sites
- Stops ad networks
- Always check `is_domain_blacklisted(url)` before following external links

### 2. User Tier System

**Users have tier-based access**:

| Tier | Crawl Limit | Access |
|------|-------------|--------|
| Free (`is_admin=false`) | 3 total crawls, 50 pages max | Basic features |
| Admin (`is_admin=true`) | Unlimited | All features + user management |

**Implementation**:
- `backend/app/api/routes/crawls.py` - `FREE_CRAWL_LIMIT = 3` and `FREE_MAX_PAGES = 50` constants
- `/crawls/usage` endpoint returns current usage info
- Frontend shows remaining crawls in CrawlsPage and CrawlNewPage
- Limit check happens in `create_crawl()` before creating new crawl

**New user defaults**: `is_admin=false` (free tier)

### 3. Row Level Security (RLS)

**ALL database tables use RLS**. When working with the database:

- Use `auth_client = get_auth_client()` for user-scoped operations
- Use `service_client` (service role key) for admin/system operations
- Never bypass RLS in production code without explicit justification

### 4. Non-HTML Content Handling

**PDFs and other non-HTML files** require special handling:

- **Crawler** (`backend/app/services/crawler.py`): Skips HTML parsing for non-HTML content types, creates filename-based titles
- **Issue Detector** (`backend/app/services/issue_detector.py`): `_is_html_page()` checks both content-type AND URL extension

**URL extensions that skip HTML checks**:
`.pdf`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`, `.mp4`, `.mp3`, `.wav`, `.zip`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.csv`, `.json`, `.xml`

**Why this matters**: PDFs should not be flagged for "missing H1" or "thin content" - these are HTML-specific issues.

### 5. Python Bytecode Caching

**Problem**: After updating Python code, old bytecode (`*.pyc`) may persist.

**Solution**: Clear cache after significant changes:

```bash
# Clear all __pycache__ directories
powershell -Command "Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force"

# Clear all .pyc files
powershell -Command "Get-ChildItem -Path . -Filter *.pyc -Recurse -File | Remove-Item -Force"
```

### 6. Logging Verbosity

**Issue**: httpx logs every HTTP request at INFO level (creates spam).

**Solution**: Set logging level for noisy libraries:

```python
import logging

# In main.py and worker.py
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)
```

---

## Development Workflow

### Starting the Application

**Start servers**:

```bash
start.bat  # Starts frontend (port 3000) + backend (port 8000)
```

**Stop servers**:

- Press Ctrl+C in the terminal running start.bat
- Wait 5 seconds for processes to fully stop

### Making Changes

1. **Backend changes** (Python):

   - Edit files in `backend/app/`
   - Backend auto-reloads with Uvicorn `--reload`
   - Background crawl tasks run in-process (no separate worker)

2. **Frontend changes** (TypeScript/React):

   - Edit files in `frontend/src/`
   - Hot reload automatic (React Fast Refresh)

3. **Database schema changes**:
   - Create SQL migration in `database/migrations/`
   - **Run migration directly via Supabase CLI** (Claude has access)
   - Update Pydantic models in `backend/app/models/models.py`

### Testing Changes

1. **Test in browser**: http://localhost:3000
2. **Check backend logs** for errors
3. **Verify database** changes in Supabase dashboard
4. **Test end-to-end** by creating a crawl

---

## Common Pitfalls & Solutions

### Pitfall #1: Field Name Mismatches

**Symptom**: `{'code': 'PGRST204', 'message': "Could not find the 'finished_at' column"}`

**Cause**: Code uses `finished_at` but database has `completed_at`

**Solution**:

1. Query database to verify actual column names
2. Update Pydantic models to match database
3. Update all code references
4. Clear Python bytecode cache
5. Restart servers

### Pitfall #2: HTML Storage Path Column Name

**Symptom**: Semantic strategy analysis produces no results (section missing from report)

**Cause**: Migration defines `html_storage_path`, crawler historically wrote `html_snapshot_path`. Production DB may have either or both.

**Solution**: Always check BOTH column names when querying:
```python
path = r.get("html_storage_path") or r.get("html_snapshot_path")
```

As of March 2026, the crawler writes `html_storage_path` (correct). The report queries both for backwards compatibility.

### Pitfall #3: Empty Content Showing on Docs Page

**Symptom**: Docs page shows blank content area

**Cause**: `activeSection` state initialized incorrectly

**Solution**: Set initial state to actual doc item ID:

```typescript
const [activeSection, setActiveSection] = useState<string>("overview"); // ✅
```

### Pitfall #3: Slow Database Operations

**Symptom**: Crawl takes 10+ minutes for 100 pages

**Cause**: Individual database inserts instead of batching

**Solution**: Use batch operations:

```python
# Batch save links
await self._save_links_batch(links_to_save)  # ONE call

# Batch save images
await self._save_images_batch(images_to_save)  # ONE call
```

### Pitfall #4: External Link Infinite Crawl

**Symptom**: Crawler never stops, crawls thousands of pages

**Cause**: Following external links without limits

**Solution**:

1. Check `is_domain_blacklisted(url)` before following
2. Enforce `max_external_links` limit
3. Track external domains in `self.external_domains_crawled`
4. Only go 1 level deep on external sites (`external_depth = 1`)

---

## File Structure

```
ai-webscraper/
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── contexts/         # React Context (Auth)
│   │   ├── pages/           # Route pages
│   │   ├── services/        # API client
│   │   └── App.tsx          # Main app component
│   └── public/              # Static assets
│
├── backend/                   # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   │   └── routes/     # Endpoint definitions
│   │   ├── core/           # Core utilities (auth, config, blacklist)
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic (crawler, worker)
│   │   └── main.py         # FastAPI app entry point
│   └── requirements.txt     # Python dependencies
│
├── database/                  # Database migrations
│   └── migrations/           # SQL migration files
│
├── docker-compose.yml         # Local dev compose (backend only)
├── start.bat                  # Start all servers (local dev)
└── CLAUDE.md                 # This file
```

---

## Deployment — Hetzner VPS

- **Host:** `178.156.192.117`
- **SSH:** `ssh deploy@178.156.192.117`
- **VPS path:** `~/apps/ai-webscraper/`
- **Orchestration:** `~/apps/cushlabs-prod-server/docker-compose.yml`
- **Domain:** `scraper.cushlabs.ai` (HTTPS via Caddy/Let's Encrypt)
- **Docker service/container name:** `webscraper`
- **Internal port:** `10000` (bound to `127.0.0.1`, set via `PORT=10000` in compose environment)
- **Docker image:** `mcr.microsoft.com/playwright/python:v1.50.0-noble` (~3GB, builds are slow)
- **Database:** Supabase (external, not self-hosted) — Project: `cushlabs-site-analysis`
- **Caddy config:** `/etc/caddy/Caddyfile` on the VPS

### Architecture

- **Caddy** serves the static React build at `/` and proxies `/api/*` to the backend container
- Caddy rewrites `/api/v1/<endpoint>` to add trailing slashes internally, preventing FastAPI 307 redirects from dropping auth headers
- **Static frontend location:** `/home/deploy/apps/static/webscraper/`
- **Backend** runs in Docker, listening on port 10000 (not exposed publicly)
- **Background tasks** run in-process using `asyncio.create_task()` (no Celery/Redis)
- **Vitals tracker** already integrated in `index.html`

### Deploy Backend

```bash
ssh deploy@178.156.192.117 'cd ~/apps/ai-webscraper && git pull && cd ~/apps/cushlabs-prod-server && docker compose up -d --build webscraper'
```

Code changes require `--build`. Config-only changes (env vars) just need `docker compose restart webscraper`.

### Deploy Frontend

Build locally, then copy static files to VPS:

```bash
cd frontend
DISABLE_ESLINT_PLUGIN=true REACT_APP_API_URL=https://scraper.cushlabs.ai/api/v1 npm run build
scp -r build/* deploy@178.156.192.117:~/apps/static/webscraper/
```

### Health Check

```bash
curl https://scraper.cushlabs.ai/api/v1/health/
# Trailing slash required
```

### Logs

```bash
ssh deploy@178.156.192.117 'docker logs -f webscraper'
```

### Required Env Vars (backend)

See `backend/.env.example` for the full list. Key vars:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (admin ops) |
| `OPENAI_API_KEY` | For LLM-powered analysis |
| `CORS_ORIGINS` | Allowed origins (set to `https://scraper.cushlabs.ai`) |
| `ENVIRONMENT` | `production` |
| `PORT` | `10000` (set in compose, not .env) |

### Resource Notes

- VPS has 4GB RAM total, ~350MB used — be mindful before adding services
- Docker network: services talk to each other via Docker service names (e.g., `redis://redis:6379`), not localhost

---

## Key Files to Know

### Deployment

- `backend/Dockerfile` - Docker build (Playwright base image)
- `backend/app/core/config.py` - CORS origins, environment config
- `backend/.env.example` - Required backend environment variables
- `frontend/.env.example` - Required frontend build-time variables

### Backend

- `backend/app/main.py` - FastAPI app, logging config
- `backend/app/services/worker.py` - Background crawl tasks (async, no Celery)
- `backend/app/services/crawler.py` - Core crawling logic
- `backend/app/services/issue_detector.py` - SEO issue detection
- `backend/app/services/semantic_builder.py` - Pure Python: extract headings, CTAs, infer page purpose from URL patterns
- `backend/app/services/llm_service.py` - LLM abstraction with `generate_executive_summary()` + `analyze_page_strategy()`
- `backend/app/core/domain_blacklist.py` - Blacklisted domains
- `backend/app/core/llm_config.py` - LLM task configs, model selection, cost tracking
- `backend/app/models/models.py` - Pydantic models
- `backend/app/models/llm_models.py` - LLM structured output models (ExecutiveSummary, PageSemanticStrategy, etc.)
- `backend/app/api/routes/crawls.py` - Crawl API endpoints (includes usage endpoint)
- `backend/app/api/routes/analysis.py` - AI report generation (Phase 1-4 pipeline)

### Frontend

- `frontend/src/App.tsx` - Routes and auth setup
- `frontend/src/contexts/AuthContext.tsx` - Authentication state
- `frontend/src/services/api.ts` - API client
- `frontend/src/pages/CrawlDetailPage.tsx` - Main crawl detail view

### Database

- `database/migrations/PRODUCTION_READY_MIGRATION.sql` - Base schema
- `database/migrations/004_enhance_rls_policies.sql` - RLS policies
- `database/migrations/005_external_link_limits.sql` - External link safety

---

## Communication Style

### Code Comments

- **Why, not what**: Explain reasoning, not obvious syntax
- **Flag gotchas**: Warn about common mistakes
- **Link to docs**: Reference external documentation when relevant

**Good**:

```python
# Fixed: Database uses completed_at (not finished_at)
"completed_at": datetime.now().isoformat()
```

**Bad**:

```python
# Set completed_at to current time
"completed_at": datetime.now().isoformat()
```

### Commit Messages

- Use conventional commits format
- Be specific about what changed and why

**Examples**:

- `fix: Use completed_at field to match database schema`
- `feat: Add batch insert for links to improve performance`
- `docs: Update CLAUDE.md with external link safety patterns`

---

## When to Ask Questions

**Ask first only for**:

1. Destructive operations (DROP TABLE, database resets)
2. Changes affecting production authentication
3. Removing features that might be intentionally designed
4. Major architectural changes

**Just do it** (execute directly, don't ask):

1. Fixing bugs - make the fix
2. Database migrations - run them via Supabase CLI
3. RLS policy fixes - execute the SQL
4. Performance improvements - implement and apply
5. Schema additions - create and run migration
6. Linter warnings - fix and deploy
7. Security fixes - implement immediately

---

## Emergency Recovery

### Backend Won't Start

1. Check for Python syntax errors in recent changes
2. Clear `__pycache__` directories
3. Check Supabase connection in `.env`

### Frontend Won't Compile

1. Check for TypeScript errors: `npm run build`
2. Clear node modules: `rm -rf node_modules && npm install`
3. Check case sensitivity in imports

### Database Connection Issues

1. Verify Supabase credentials in `.env`
2. Check RLS policies aren't blocking operations
3. Use service role key for admin operations

### Crawl Stuck/Never Completes

1. Check backend server logs for background task errors
2. Clear Python bytecode cache
3. Verify `completed_at` field is being set (not `finished_at`)
4. Check for infinite loops in external link following

---

## Success Metrics

A well-implemented feature should:

- ✅ **Work correctly** on first try (test thoroughly)
- ✅ **Match database schema** exactly (verify field names)
- ✅ **Use batch operations** where possible (performance)
- ✅ **Handle errors gracefully** (don't crash, log clearly)
- ✅ **Follow existing patterns** (consistency)
- ✅ **Document gotchas** (help future developers)

---

## Devin's DeepWiki Notes

https://deepwiki.com/RCushmaniii/ai-resume-tailor

---

**Last Updated**: March 28, 2026
**Maintained By**: Claude (Anthropic) + CushLabs Team
