# AI Web Scraper - Claude Context Guide

> **Purpose**: This document provides context for AI assistants (like Claude) working on this codebase. It documents conventions, patterns, and critical knowledge to maintain consistency and quality.

---

## Project Overview

**AI Web Scraper by CushLabs** is an admin-only web crawling and site analysis platform designed for internal use.

### Core Mission

- Crawl websites starting from a URL
- Extract and store page content for inspection
- Detect high-signal SEO and technical issues
- Provide lightweight heuristics for prioritization

### Explicit Non-Goals (v1)

- ❌ Selector-based scraping
- ❌ Client-facing reports or exports
- ❌ Real-time dashboards with WebSockets
- ❌ AI-driven scoring (feature-flagged off by default)

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
- **Task Queue**: Celery + Redis
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

### 2. Row Level Security (RLS)

**ALL database tables use RLS**. When working with the database:

- Use `auth_client = get_auth_client()` for user-scoped operations
- Use `service_client` (service role key) for admin/system operations
- Never bypass RLS in production code without explicit justification

### 3. Python Bytecode Caching

**Problem**: After updating Python code, old bytecode (`*.pyc`) may persist.

**Solution**: Clear cache after significant changes:

```bash
# Clear all __pycache__ directories
powershell -Command "Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force"

# Clear all .pyc files
powershell -Command "Get-ChildItem -Path . -Filter *.pyc -Recurse -File | Remove-Item -Force"
```

### 4. Logging Verbosity

**Issue**: httpx logs every HTTP request at INFO level (creates spam).

**Solution**: Set logging level for noisy libraries:

```python
import logging

# In main.py and worker.py
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.WARNING)
```

---

## Development Workflow

### Starting the Application

**Start servers**:

```bash
start.bat  # Starts frontend (port 3000) + backend (port 8000) + Celery worker
```

**Stop servers**:

- Press Ctrl+C in the terminal running start.bat
- Wait 5 seconds for processes to fully stop

### Making Changes

1. **Backend changes** (Python):

   - Edit files in `backend/app/`
   - Backend auto-reloads with Uvicorn `--reload`
   - **Exception**: Celery worker requires restart for changes

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

### Pitfall #2: Empty Content Showing on Docs Page

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
├── start.bat                  # Start all servers
└── CLAUDE.md                 # This file
```

---

## Key Files to Know

### Backend

- `backend/app/main.py` - FastAPI app, logging config
- `backend/app/services/worker.py` - Celery crawl task
- `backend/app/services/crawler.py` - Core crawling logic
- `backend/app/core/domain_blacklist.py` - Blacklisted domains
- `backend/app/models/models.py` - Pydantic models
- `backend/app/api/routes/crawls.py` - Crawl API endpoints

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
3. Restart Redis: `redis-server`
4. Check Supabase connection in `.env`

### Frontend Won't Compile

1. Check for TypeScript errors: `npm run build`
2. Clear node modules: `rm -rf node_modules && npm install`
3. Check case sensitivity in imports

### Database Connection Issues

1. Verify Supabase credentials in `.env`
2. Check RLS policies aren't blocking operations
3. Use service role key for admin operations

### Crawl Stuck/Never Completes

1. Check Celery worker logs
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

**Last Updated**: January 11, 2026
**Maintained By**: Claude (Anthropic) + CushLabs Team
