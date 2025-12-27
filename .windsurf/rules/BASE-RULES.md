# 🧠 AI WebScraper — Engineering Rules (v1.0)

## 1. Manifesto

- **Project:** AI WebScraper (CushLabs Site Analysis)
- **Philosophy:** "Crawl. Inspect. Prioritize." — Boring is good. Explicit > clever. Secure by default.
- **Scope:** Internal admin-only tool. High-signal analysis, not noisy reports. v1 is opinionated and feature-limited by design.

## 2. Tech Stack (Strict)

### Backend
- **Framework:** FastAPI 0.104.1+ (Python 3.8+)
- **Server:** Uvicorn (ASGI)
- **Validation:** Pydantic v2 (mandatory for all requests/responses)
- **Background Jobs:** Celery 5.3.4 + Redis
- **Database:** Supabase (PostgreSQL with Row Level Security)
- **Scraping:** BeautifulSoup4, Playwright 1.40.0, Trafilatura, HTTPX
- **Optional:** OpenAI (feature-flagged)

### Frontend
- **Framework:** React 18.2.0 with TypeScript (strict)
- **Routing:** React Router v6
- **Styling:** TailwindCSS
- **State:** Zustand (minimal usage, prefer server state)
- **Auth:** Supabase JS client
- **HTTP:** Axios

### Infrastructure
- **Database:** Supabase PostgreSQL
- **Message Broker:** Redis (for Celery)
- **Storage:** Local filesystem for HTML snapshots/screenshots
- **Deployment:** Backend (Heroku/Cloud Run), Frontend (Vercel/Netlify)

## 3. Architecture Principles

### Backend (FastAPI)
- **Service Layer Pattern:** Separate routes, services, models, scrapers
  - `api/routes/` - Route handlers (thin, delegate to services)
  - `services/` - Business logic (crawler, worker, storage, SEO, LLM)
  - `models/` - Pydantic models + SQL schema
  - `scrapers/` - Base scraper classes
  - `core/` - Config, auth middleware
  - `db/` - Supabase client singleton
- **Async-First:** Use `async`/`await` for all I/O operations
- **Type Safety:** Type hints on all functions, Pydantic for validation
- **Background Processing:** Long-running crawls execute via Celery workers

### Frontend (React)
- **Component Architecture:** Functional components with hooks
- **State Management Priority:** Server state > URL state > Local state
  - Avoid global client state unless justified
- **Code Organization:**
  - `pages/` - Page-level components
  - `components/` - Reusable UI components
  - `contexts/` - AuthContext only (minimal)
  - `services/` - API service layer (Axios wrappers)
  - `lib/` - Supabase client setup

### Separation of Concerns
- **UI Layer:** React components render UI only
- **Logic Layer:** Custom hooks and services handle business logic
- **Data Layer:** API services communicate with backend
- **Auth Layer:** Supabase Auth + JWT tokens

## 4. Data Fetching & API Design

### Backend API Conventions
- **Base URL:** `/api/v1`
- **Response Structure:** Consistent JSON responses
  - Success: `{ "data": {...} }`
  - Error: `{ "detail": "message" }` (FastAPI standard)
- **Authentication:** JWT tokens from Supabase Auth
- **Validation:** Pydantic models validate all inputs
- **Error Handling:** Log internally, return safe messages to client

### Frontend API Calls
- **Centralized Services:** Use `services/` layer, not direct Axios calls in components
- **Error Handling:** Surface actionable feedback to users
- **Loading States:** Always handle pending/success/error states
- **Auth Headers:** Include JWT token in Authorization header

### Background Jobs (Celery)
- **Long-Running Tasks:** Crawls run in Celery workers
- **Status Updates:** Track job status in database
- **Error Recovery:** Log failures, allow retry mechanisms
- **Idempotency:** Tasks should be safe to retry

## 5. Database & Security

### Supabase Integration
- **RLS Enforcement:** All tables have Row Level Security enabled
- **User Ownership:** Queries filter by `user_id` (RLS policies enforce)
- **Service Role Key:** Backend uses service role key for admin operations
- **Anon Key:** Frontend uses anon key for client-side auth
- **No RLS Bypass:** Never disable RLS for convenience

### Authentication & Authorization
- **Admin-Only Platform:** v1 is single-tenant, admin users only
- **Role Model:** Minimal — `user`, `admin` (isAdmin flag)
- **Protected Routes:** Frontend wraps routes with `<ProtectedRoute>`
- **API Auth:** Backend verifies JWT on protected endpoints
- **Session Management:** Supabase Auth handles sessions

### Data Security
- **Input Validation:** Pydantic validates all request data
- **SQL Injection Prevention:** Parameterized queries via Supabase client
- **XSS Protection:** Sanitize content before storage
- **Sensitive Data:** Never expose API keys, credentials to frontend
- **Content Storage:** HTML snapshots stored securely with access control

## 6. Feature Flags (Opinionated Scope Control)

### v1 Core Features (Always Enabled)
- Content-first crawling
- Page inventory with metadata
- Link analysis
- Issue detection (thin content, missing metadata, broken links)
- HTML snapshot storage

### Gated Features (Disabled by Default)
Control via environment variables:

- `ENABLE_BATCH_CRAWLS=false` - Batch crawling operations
- `ENABLE_SEO_AUDIT=false` - SEO audit scoring system
- `ENABLE_LLM=false` - OpenAI-powered content summaries
- `ENABLE_SELECTOR_SCRAPING=false` - Advanced selector-based scraping

**Rule:** Do not enable gated features without explicit discussion. v1 is intentionally minimal.

### Gated Endpoints
- `/crawls/{id}/audit` - Requires `ENABLE_SEO_AUDIT=true`
- `/crawls/{id}/summary` - Requires `ENABLE_LLM=true`
- `/batches/*` - Requires `ENABLE_BATCH_CRAWLS=true`

## 7. UI/UX Guidelines

### Design Philosophy
- **Desktop-First:** Internal tool for technical operators
- **Clean & Functional:** No unnecessary animations or flourish
- **Data-Dense:** Prioritize information density over whitespace
- **Responsive:** Must work on desktop and tablet

### Styling
- **TailwindCSS:** Utility-first approach
- **Consistent Spacing:** Use Tailwind scale (`p-4`, `m-2`, etc.)
- **Typography:** Clear hierarchy with semantic HTML
- **Colors:** Refer to `frontend/docs/BRAND.md` and `DESIGN.md` if they exist

### Accessibility
- **Semantic HTML:** Use proper elements (`<button>`, `<nav>`, etc.)
- **Keyboard Navigation:** All interactive elements accessible via keyboard
- **ARIA Labels:** Add when semantic HTML insufficient
- **Color Contrast:** Meet WCAG AA standards

## 8. Coding Standards

### Python (Backend)
- **Style:** PEP 8 compliance
- **Type Hints:** All functions must have type hints
- **Docstrings:** Use for complex functions (explain _why_, not _what_)
- **Async/Await:** Prefer async functions for I/O
- **Error Handling:** Catch specific exceptions, log with context
- **No Magic:** Explicit is better than implicit

### TypeScript (Frontend)
- **Strict Mode:** Enabled in `tsconfig.json`
- **No `any`:** Explicitly typed or use generics
- **No `@ts-ignore`:** Fix the type issue properly
- **Named Exports:** Preferred over default exports
- **Functional Components:** Use hooks, avoid class components
- **Custom Hooks:** Extract reusable logic into hooks

### General
- **DRY (Don't Repeat Yourself):** Abstract repeated logic
- **SRP (Single Responsibility):** One responsibility per function/component
- **SOLID Principles:** Follow for maintainability
- **Comments:** Explain _why_ (context), not _what_ (obvious code)
- **Descriptive Names:** Variables and functions self-document

## 9. Content Extraction & Crawling

### Scraping Strategy
- **Multi-Method Approach:**
  1. Simple HTTP (HTTPX) for static content (fastest)
  2. Playwright for JavaScript-rendered pages
  3. Selenium as fallback browser automation
  4. Trafilatura for intelligent content extraction

### Crawl Configuration
- **Respect robots.txt:** Honor website crawl rules
- **Rate Limiting:** Configurable delays between requests
- **Depth Control:** Max depth and max pages per crawl
- **Content Hashing:** Detect duplicate content
- **Evidence Preservation:** Store HTML snapshots for forensics

### Issue Detection Rules
- **High-Signal Only:** Detect obvious, defensible issues
- **Avoid Noise:** No academic SEO metrics
- **Severity Levels:** info, warning, error, critical
- **Explainable:** Every issue must have clear reasoning

## 10. Anti-Patterns (Refusal Criteria)

If asked to do any of the following, **pause, warn, and explain why**:

### Backend
- Adding complex RBAC or multi-tenant features (v1 is admin-only)
- Enabling gated features without discussion
- Bypassing RLS for convenience
- Creating synchronous endpoints for long-running tasks
- Adding unnecessary dependencies

### Frontend
- Using Redux or complex state management without demonstrated need
- Creating deeply nested component hierarchies
- Fetching data directly in components (use services)
- Adding global state when server state suffices
- Building multi-user collaboration features (out of scope for v1)

### General
- Feature bloat beyond v1 scope (see PRD non-goals)
- Premature optimization without data
- Over-engineering simple solutions
- Ignoring feature flag boundaries
- Security shortcuts or RLS bypass

## 11. Documentation Requirements

### Code Documentation
- **Docstrings:** Complex functions explain purpose and context
- **Comments:** Explain non-obvious decisions
- **Type Hints:** Self-documenting function signatures

### Project Documentation
- **PRD:** `frontend/docs/PRD.md` - Source of truth for product scope
- **Architecture:** `frontend/docs/ARCHITECTURE_AND_DESIGN_PRINCIPLES.md`
- **Tech Stack:** `frontend/docs/TECH_STACK.md`
- **Brand:** `frontend/docs/BRAND.md` - Voice and messaging
- **Design:** `frontend/docs/DESIGN.md` - UI specifications
- **Setup:** `frontend/docs/SETUP_INSTRUCTIONS.md`

### Cascade Integration
- **PROJECT_STARTUP.md:** `.windsurf/PROJECT_STARTUP.md` - Startup guide
- **Rules:** `.windsurf/rules/BASE-RULES.md` (this file)

## 12. Testing & Quality

### Backend Testing
- **Unit Tests:** Test services and utilities
- **Integration Tests:** Test API endpoints
- **Scraper Tests:** Verify content extraction logic
- **Validation:** Pydantic models validate inputs

### Frontend Testing
- **Component Tests:** Test UI components in isolation
- **Integration Tests:** Test user flows
- **Type Checking:** TypeScript strict mode catches errors

### Quality Checklist
- [ ] Code follows PEP 8 (Python) or TypeScript best practices
- [ ] All functions have type hints
- [ ] Pydantic models validate API inputs
- [ ] Feature flags respected
- [ ] RLS policies not bypassed
- [ ] Error handling implemented
- [ ] Documentation updated if needed

## 13. Development Workflow

### Local Development
```bash
# Quick start (Windows)
dev.bat  # or dev-wt.bat for Windows Terminal

# This starts:
# 1. Backend API (port 8000)
# 2. Celery Worker
# 3. Frontend (port 3000)
```

### Git Workflow
- **Branches:** Feature branches off `main`
- **Commits:** Clear, descriptive commit messages
- **PRs:** Reference issue/feature, describe changes
- **Review:** Code review required before merge

### Pre-Commit Checklist
- [ ] Code runs locally without errors
- [ ] TypeScript compiles (`npm run build`)
- [ ] Python syntax valid (`python -m py_compile`)
- [ ] No hardcoded secrets or API keys
- [ ] Feature flags respected
- [ ] Documentation updated if needed

---

## Final Instructions

### For AI Assistants (Claude, Cascade, etc.)

1. **Read Documentation First:** Consult `frontend/docs/` before implementing features
2. **Respect v1 Scope:** PRD defines strict boundaries — do not exceed them
3. **Follow Feature Flags:** Do not enable gated features without discussion
4. **Maintain Architecture:** Preserve service layer separation
5. **Type Safety:** All code must be fully typed
6. **Security First:** Never bypass RLS, always validate inputs
7. **Ask Before Breaking Rules:** If a request conflicts with these rules, pause and explain

### For Human Developers

1. **Consult PRD:** Understand product decisions and scope
2. **Follow Architecture:** Maintain clean separation of concerns
3. **Test Locally:** Use `dev.bat` for full stack
4. **Review Rules:** Reference this document during code review
5. **Update Docs:** Keep documentation current with changes

---

**Version:** 1.0
**Last Updated:** 2025-12-26
**Maintained By:** Robert Cushman

If a request conflicts with **security**, **scope discipline**, **feature flags**, or **architectural principles**: **Pause, warn, and explain before proceeding.**
