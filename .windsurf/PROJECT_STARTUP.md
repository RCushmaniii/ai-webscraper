# AI WebScraper - Cascade Startup Guide

## 🚀 Quick Context

**Project**: AI WebScraper (CushLabs Site Analysis) - Internal admin-only web crawling and analysis tool
**Repository**: Local development
**Developer**: Robert Cushman
**Location**: Guadalajara, Mexico

## 📋 Project Overview

A production-ready full-stack web crawling and site analysis application built for internal use. The tool crawls websites, extracts clean content, analyzes SEO issues, and helps prioritize improvement opportunities with evidence-based insights.

### Core Philosophy

**"Crawl. Inspect. Prioritize."**

- **Content-first crawling** - Not just URL collection, but deep content extraction
- **High-signal issue detection** - Defensible problems, not noisy SEO reports
- **Evidence storage** - HTML snapshots and screenshots for forensic analysis
- **Admin-only** - Single-tenant v1, built for technical operators

### Key Features

- **Async web crawling** with configurable depth and page limits
- **Multi-method content extraction** (static HTML + JavaScript-rendered pages)
- **Link analysis** with broken link detection
- **Issue detection** with severity classification (info/warning/error/critical)
- **Page inventory system** with metadata tracking
- **SEO audit capabilities** (feature-flagged)
- **LLM-powered summaries** (optional OpenAI integration)
- **Batch crawling operations** (gated feature)
- **Evidence preservation** (HTML snapshots, screenshots, content hashes)

## 🏗️ Architecture

```
Backend (FastAPI):  Python 3.8+ + FastAPI + Celery + Redis + Playwright
Frontend (React):   React 18 + TypeScript + TailwindCSS + React Router v6
Database:           Supabase (PostgreSQL) with Row Level Security
Storage:            Local filesystem for snapshots/screenshots
Auth:               Supabase Auth with JWT + admin-only access
Background Jobs:    Celery workers with Redis message broker
```

### Key Directories

- `backend/app/` - FastAPI application with modular structure
  - `api/routes/` - Route handlers (crawls, batches, users, health)
  - `core/` - Configuration and auth middleware
  - `db/` - Supabase client singleton
  - `models/` - Pydantic models and SQL schema
  - `scrapers/` - Base scraper classes
  - `services/` - Business logic (crawler, worker, storage, SEO, LLM)
- `frontend/src/` - React application with TypeScript
  - `components/` - Reusable UI components
  - `pages/` - 20+ page components
  - `contexts/` - AuthContext for session management
  - `services/` - API service layer
- `frontend/docs/` - Comprehensive documentation
- `.windsurf/` - Cascade configuration and rules

## 🎯 Current State

### Completed Features

- ✅ **Core Crawling Engine** - Async crawling with depth control
- ✅ **Content Extraction** - BeautifulSoup4 + Trafilatura for clean text
- ✅ **JavaScript Rendering** - Playwright integration for SPA support
- ✅ **Link Analysis** - Internal/external classification, broken link detection
- ✅ **Issue Detection** - Thin content, missing metadata, indexability problems
- ✅ **Page Inventory** - Full metadata tracking with snapshots
- ✅ **Authentication System** - Supabase Auth with admin roles
- ✅ **Background Processing** - Celery workers for long-running crawls
- ✅ **API Layer** - RESTful FastAPI endpoints with OpenAPI docs
- ✅ **React Frontend** - Modern UI with routing and state management

### Recent Work

- **Health Check Endpoint** - New `/api/v1/health` route for monitoring
- **Enhanced Auth Pages** - Signup, Login, Forgot Password, Reset Password flows
- **Brand Guidelines** - Documented in `frontend/docs/BRAND.md`
- **Design System** - UI specifications in `frontend/docs/DESIGN.md`
- **Windows Terminal Integration** - `dev-wt.bat` for improved dev experience
- **Privacy & Terms** - Legal pages with content updates
- **Supabase Client Improvements** - Singleton pattern with better error handling

### Feature Flags (Gated Features)

**Currently Disabled by Default:**
- Batch crawling operations
- SEO audit scoring system
- LLM-powered content summaries
- Advanced selector-based scraping

## 📚 Essential References

### Primary Documentation

1. **[Main README.md](../README.md)** - Project overview and quick start
2. **[PRD](../frontend/docs/PRD.md)** - Product Requirements Document with v1 scope
3. **[Architecture & Design Principles](../frontend/docs/ARCHITECTURE_AND_DESIGN_PRINCIPLES.md)** - System design philosophy
4. **[Tech Stack](../frontend/docs/TECH_STACK.md)** - Complete technology breakdown
5. **[Brand Guidelines](../frontend/docs/BRAND.md)** - Voice, messaging, and positioning
6. **[Design System](../frontend/docs/DESIGN.md)** - UI/UX specifications

### Key Setup Files

- `frontend/docs/SETUP_INSTRUCTIONS.md` - Detailed development setup
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies
- `backend/.env` - Backend environment configuration
- `frontend/.env` - Frontend environment configuration

### Database Schema

- `backend/app/models/schema.sql` - Complete PostgreSQL schema with RLS policies

## 🔧 Development Workflow

### Quick Start

```bash
# Option 1: Use Windows batch script (recommended)
dev.bat

# Option 2: Use Windows Terminal (opens 3 separate tabs)
dev-wt.bat

# This starts:
# 1. Backend API (FastAPI + Uvicorn on port 8000)
# 2. Celery Worker (background job processor)
# 3. Frontend React app (Vite dev server on port 3000)
```

### Manual Startup

```bash
# Backend API (Terminal 1)
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker (Terminal 2)
cd backend
venv\Scripts\activate
celery -A app.worker worker --loglevel=info

# Frontend (Terminal 3)
cd frontend
npm install
npm run dev
```

### Development URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

### Key Environment Variables

**Backend (.env):**
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Feature Flags
ENABLE_BATCH_CRAWLS=false
ENABLE_SEO_AUDIT=false
ENABLE_LLM=false

# Optional
OPENAI_API_KEY=your-openai-key  # Only if ENABLE_LLM=true
STORAGE_DIR=storage              # Default: ./storage
```

**Frontend (.env):**
```env
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
REACT_APP_API_URL=http://localhost:8000/api/v1
```

### Verification Commands

```bash
# Frontend type checking and build
cd frontend && npm run build

# Backend health check
curl http://localhost:8000/api/v1/health

# Check Celery worker
celery -A app.worker inspect active

# Run Python syntax check
python -m py_compile backend/app/main.py
```

## 🎨 Design & Brand Guidelines

### Brand Voice

**From `frontend/docs/BRAND.md`:**
- **Tone**: Direct, no-nonsense, technically competent
- **Positioning**: Internal tool for technical operators
- **Messaging**: "High-signal analysis without the noise"

### UI Principles

**From `frontend/docs/DESIGN.md`:**
- Clean, modern interface with TailwindCSS
- Responsive design for desktop-first workflow
- Accessibility standards (ARIA labels, keyboard navigation)
- Consistent component patterns

## 🔐 Authentication & Security

### Supabase Auth Implementation

- **Frontend**: AuthContext provider with session management
- **Protected Routes**: ProtectedRoute wrapper component
- **Admin-Only Access**: isAdmin flag checked on protected routes
- **JWT Tokens**: Passed to backend via Authorization headers
- **Auto-Refresh**: Session renewal handled automatically

### Security Features

- **Row Level Security (RLS)** - All tables enforce user ownership
- **API Authentication** - JWT verification on protected endpoints
- **Input Validation** - Pydantic models validate all request data
- **Rate Limiting** - Respect for robots.txt and configurable delays
- **SQL Injection Prevention** - Parameterized queries via Supabase client
- **XSS Protection** - Content sanitization before storage

### User Roles

- **Admin Users** - Full platform access (isAdmin=true)
- **Regular Users** - Limited access (v1 may not use this tier)

## 🕷️ Crawling Architecture

### Scraper Strategy

**Multi-Method Approach:**
1. **Simple HTTP** - HTTPX for static content (fastest)
2. **BeautifulSoup4** - HTML parsing and link extraction
3. **Playwright** - JavaScript-rendered pages (headless browser)
4. **Selenium** - Fallback browser automation
5. **Trafilatura** - Intelligent content extraction

### Content Extraction Pipeline

```
URL → Fetch HTML → Parse with BS4 → Extract with Trafilatura → Clean Text
                                   ↓
                           Store Snapshot → Calculate Hash → Detect Duplicates
```

### Issue Detection Rules

**Automated Checks:**
- Missing or duplicate titles
- Thin content (< 300 words threshold)
- Missing meta descriptions
- Non-indexable pages
- Broken internal/external links
- Orphaned pages (no incoming links)

**Severity Levels:**
- `info` - Informational notices
- `warning` - Should be addressed
- `error` - Significant problems
- `critical` - Immediate attention required

## 🚀 Deployment

### Recommended Platforms

**Backend:**
- Heroku (easiest for Celery + Redis)
- Google Cloud Run (serverless)
- AWS Elastic Beanstalk
- DigitalOcean App Platform

**Frontend:**
- Vercel (recommended for React)
- Netlify
- Firebase Hosting
- GitHub Pages

**Database:**
- Supabase (already configured)

### Pre-Deployment Checklist

- [ ] Environment variables configured on hosting platform
- [ ] Supabase RLS policies verified
- [ ] Redis instance provisioned (for Celery)
- [ ] CORS origins configured for production URLs
- [ ] Admin user created in Supabase
- [ ] Feature flags set appropriately
- [ ] Storage directory configured with write permissions

### Environment-Specific Configuration

**Production Backend:**
- Set `ENABLE_BATCH_CRAWLS`, `ENABLE_SEO_AUDIT`, `ENABLE_LLM` as needed
- Use production Redis URL
- Configure production Supabase credentials
- Set appropriate log levels

**Production Frontend:**
- Update `REACT_APP_API_URL` to production backend
- Use production Supabase anon key
- Build with `npm run build`
- Configure hosting platform for SPA routing

## 🎛️ Cascade-Specific Guidelines

### When Working on This Project

1. **Consult documentation first** - Comprehensive docs in `frontend/docs/`
2. **Follow opinionated design** - v1 explicitly avoids feature bloat
3. **Respect feature flags** - Don't enable gated features without discussion
4. **Maintain admin-only focus** - No public/multi-tenant features in v1
5. **Preserve evidence storage** - HTML snapshots and content hashes are critical
6. **Test with Celery running** - Background jobs are core to functionality

### Common Tasks

**Adding New API Endpoints:**
1. Create route handler in `backend/app/api/routes/`
2. Add Pydantic request/response models in `backend/app/models/`
3. Implement business logic in `backend/app/services/`
4. Register route in `backend/app/api/api.py`
5. Update frontend service in `frontend/src/services/`

**Adding New Frontend Pages:**
1. Create page component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Wrap with `<ProtectedRoute>` if auth required
4. Update navigation in `frontend/src/components/Layout.tsx`

**Modifying Database Schema:**
1. Update `backend/app/models/schema.sql`
2. Update Pydantic models in `backend/app/models/`
3. Run migration in Supabase dashboard
4. Update RLS policies if needed

**Enabling Gated Features:**
1. Set appropriate feature flag in `backend/.env`
2. Verify dependent services are configured (e.g., OpenAI API key for LLM)
3. Test thoroughly before production deployment
4. Update documentation to reflect new capabilities

### File Organization Rules

- **Single README.md** - In project root only
- **Descriptive filenames** - No generic names in subdirectories
- **Consolidated docs** - All documentation in `frontend/docs/`
- **Service layer** - Business logic stays in `backend/app/services/`
- **Route handlers** - Keep thin, delegate to services

### Coding Conventions

**Backend (Python):**
- PEP 8 style guide
- Type hints on all functions
- Pydantic for data validation
- Async/await for I/O operations
- Descriptive variable names

**Frontend (TypeScript):**
- Functional components with hooks
- TypeScript strict mode
- Named exports preferred
- Component composition over inheritance
- Custom hooks for reusable logic

## 🔍 Quick Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python virtual environment is activated
- Verify all dependencies: `pip install -r requirements.txt`
- Confirm Supabase credentials in `.env`
- Check port 8000 is not already in use

**Celery worker errors:**
- Ensure Redis is running: `redis-cli ping` (should return PONG)
- Check `CELERY_BROKER_URL` in `.env`
- Verify Celery imports: `celery -A app.worker inspect active`

**Frontend auth issues:**
- Verify Supabase anon key in frontend `.env`
- Check CORS configuration in backend
- Clear browser localStorage and retry
- Confirm user has `isAdmin=true` in Supabase users table

**Crawl jobs not processing:**
- Check Celery worker is running
- Verify Redis connection
- Check backend logs for task errors
- Ensure target website allows crawling (robots.txt)

**Database connection errors:**
- Verify Supabase service role key (not anon key) in backend
- Check Supabase project is active
- Confirm RLS policies are not blocking queries
- Test connection: `curl https://your-project.supabase.co`

**Playwright/Selenium issues:**
- Install browser binaries: `playwright install chromium`
- Check headless browser dependencies on Linux
- Verify sufficient memory for browser automation
- Try increasing timeout values in scraper config

### Debug Commands

```bash
# Test backend health
curl http://localhost:8000/api/v1/health

# Check Celery status
celery -A app.worker inspect stats

# Test Redis connection
redis-cli ping

# Verify Supabase connection (from backend)
python -c "from app.db.supabase import get_supabase_client; print(get_supabase_client())"

# Frontend build test
cd frontend && npm run build

# Check Python syntax
python -m py_compile backend/app/main.py

# View Celery logs
celery -A app.worker worker --loglevel=debug

# Test Playwright
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### Logs Location

- **Backend API**: Console output from uvicorn
- **Celery Worker**: Console output or configured log file
- **Frontend Dev**: Vite dev server console
- **Browser Console**: React app runtime errors

---

## 📊 Database Schema Reference

### Core Tables

**crawls** - Crawl job configurations
- `id`, `user_id`, `base_url`, `status`, `max_depth`, `max_pages`
- `created_at`, `started_at`, `completed_at`

**pages** - Individual crawled pages
- `id`, `crawl_id`, `url`, `title`, `h1`, `meta_description`
- `status_code`, `word_count`, `content_hash`, `excerpt`
- `is_indexable`, `has_thin_content`

**links** - Link relationships
- `id`, `crawl_id`, `source_page_id`, `target_url`, `anchor_text`
- `link_type` (internal/external), `is_broken`, `http_status`

**issues** - Detected problems
- `id`, `crawl_id`, `page_id`, `issue_type`, `severity`
- `message`, `details_json`

**seo_metadata** - SEO-specific data
- `id`, `page_id`, `canonical_url`, `og_title`, `og_description`
- `meta_robots`, `h1_count`, `h2_count`

### Optional Tables (Feature-Flagged)

**summaries** - LLM-generated content summaries
**batches** - Batch crawl operations
**batch_sites** - Sites within batches
**audit_log** - User action tracking
**google_places** - Google Places integration

---

## 🎓 Learning Resources

### Internal Documentation

- **PRD** - Understand product decisions and v1 scope
- **Architecture Doc** - System design philosophy and trade-offs
- **Tech Stack Doc** - Why each technology was chosen
- **Brand Doc** - Voice and positioning guidelines
- **Design Doc** - UI patterns and component standards

### External References

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Supabase Docs**: https://supabase.com/docs
- **Celery Docs**: https://docs.celeryproject.org/
- **Playwright Docs**: https://playwright.dev/python/
- **Trafilatura Docs**: https://trafilatura.readthedocs.io/

---

## 📞 Project Context

**Developer**: Robert Cushman
**Location**: Guadalajara, Mexico
**Purpose**: Internal tool for website analysis and SEO auditing
**Tech Stack**: Modern full-stack with FastAPI, React, Supabase, and async task processing
**Stage**: Active development - v1 feature-complete, enhancement phase

---

## 🏁 Quick Start Checklist

**First Time Setup:**

- [ ] Clone repository
- [ ] Create Supabase project
- [ ] Run schema.sql in Supabase SQL editor
- [ ] Create admin user in Supabase Auth
- [ ] Set `isAdmin=true` in users table
- [ ] Install Redis locally or use hosted instance
- [ ] Configure backend `.env` file
- [ ] Configure frontend `.env` file
- [ ] Install Python dependencies: `pip install -r backend/requirements.txt`
- [ ] Install Node dependencies: `cd frontend && npm install`
- [ ] Install Playwright browsers: `playwright install chromium`
- [ ] Run `dev.bat` or `dev-wt.bat`
- [ ] Access frontend at http://localhost:3000
- [ ] Login with admin credentials
- [ ] Create test crawl to verify setup

**Daily Development:**

1. Start Redis (if not auto-starting)
2. Run `dev.bat` or `dev-wt.bat`
3. Access http://localhost:3000
4. Check Celery worker is processing jobs
5. Monitor backend logs for errors

---

_Last Updated: 2025-12-26 - Always reference frontend/docs/ for the most current technical documentation_
