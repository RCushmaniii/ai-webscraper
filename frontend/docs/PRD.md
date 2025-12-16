---

# 🧾 PRD.md

**Project:** CushLabs Site Analysis (Internal Tool Edition)

---

## Product Definition (One Sentence)

CushLabs Site Analysis is an **internal, admin-only site analysis tool** that crawls websites to retrieve clean page content, analyzes that content for obvious technical and SEO issues, identifies which pages matter most, and surfaces the highest-impact opportunities for improvement or competitive insight.

This is **not** a public SaaS and **not** a general-purpose scraper.

---

## Problem Statement

When evaluating a website (your own, a client’s, or a competitor’s), it is surprisingly difficult to:

- Quickly retrieve _all relevant page content_ in a structured way
- Understand which pages actually matter
- Identify obvious, high-impact technical or SEO issues without noise
- Keep durable evidence of what existed at a point in time

Existing tools either:

- Focus on shallow metrics without giving you the content, or
- Overwhelm you with exhaustive SEO reports that obscure decision-making

This project exists to support **clear thinking and prioritization**, not to replace expertise.

---

## Target User

### Primary (Only, v1)

- A **single technical operator** (you)
- Comfortable with admin dashboards and raw data
- Running audits on:

  - your own sites
  - client sites
  - competitor sites

No multi-user collaboration is assumed in v1.

---

## Core Outcomes (What Success Looks Like)

After running the tool, the operator should walk away with:

- A **mental map of the site**
- A **content inventory** they can reason about
- A **short list of real, relevant problems**
- A **prioritized action list** (“biggest bang for the buck”)
- Stored evidence of:

  - what content existed
  - what conclusions were drawn

---

## Core Capabilities (v1 – Opinionated)

### 1. Content-First Crawling

- Crawl a site starting from a URL
- Retrieve **clean, extracted text content** for each page
- Associate content with:

  - URL
  - status code
  - basic metadata (title, H1, word count)

> Crawling exists to retrieve analyzable content — not just URLs.

---

### 2. Page Inventory

Each page record includes:

- URL
- HTTP status
- Title / H1
- Word count
- Extracted text content
- Crawl run metadata (timestamp, run ID)

This inventory is the **primary dataset**.

---

### 3. Page Importance Heuristics (Lightweight)

Provide simple signals to answer:

> “Which pages matter most?”

Examples:

- Internal link count
- URL depth
- Content length
- Presence in navigation (if detectable)

No advanced SEO scoring in v1.

---

### 4. Obvious Issue Detection (High Signal Only)

Detect **clear, defensible issues**, such as:

- Missing or junk titles
- Extremely thin content
- Broken pages expected to work
- Pages unintentionally non-indexable

Explicitly avoid noisy or academic SEO metrics.

---

### 5. Opportunity Framing

Surface insights as:

- “These issues affect the most important pages”
- “Fixing X would impact Y pages”
- “This area appears weaker/stronger relative to peers” (heuristic, not absolute)

Rule-based is acceptable in v1.

---

### 6. Evidence Storage

- Extracted text content is always stored
- Raw HTML snapshots are optional and secondary
- Crawl runs are persisted for later inspection

---

## Non-Goals (Explicit v1 Exclusions)

This project deliberately does **not** include:

- Selector-based scraping tasks
- General-purpose scraping APIs
- Client-facing reports or exports
- Billing or subscriptions
- Multi-tenant user systems
- Advanced SEO scoring models
- Real-time updates or WebSockets
- Mandatory AI-generated insights

These may exist in future phases, but **not in v1**.

---

## v1 Contract (Authoritative)

### API Surface (Mounted)

**Base URL:** `http://localhost:8000/api/v1`

**Crawls**:

- `POST /crawls`
- `GET /crawls`
- `GET /crawls/{crawl_id}`
- `DELETE /crawls/{crawl_id}`
- `GET /crawls/{crawl_id}/pages`
- `GET /crawls/{crawl_id}/links`
- `GET /crawls/{crawl_id}/issues`
- `GET /crawls/{crawl_id}/html/{page_id}`
- `GET /crawls/{crawl_id}/screenshot/{page_id}`

**Users**:

- `GET /users/me`

### Feature Flags (Default Off)

These exist in the codebase but are disabled by default in v1:

- `ENABLE_BATCH_CRAWLS`
- `ENABLE_SELECTOR_SCRAPING`
- `ENABLE_SEO_AUDIT`
- `ENABLE_LLM`

### Gated Endpoints (Return 404 Unless Enabled)

- `GET /crawls/{crawl_id}/audit` requires `ENABLE_SEO_AUDIT=true`
- `GET /crawls/{crawl_id}/summary` requires `ENABLE_LLM=true`

---

## Quality Bar (Definition of “Done”)

### Correctness

- Crawls retrieve real content reliably
- Stored data matches what was actually fetched
- Analysis results are explainable

### Maintainability

- Clear separation between:

  - crawling
  - content extraction
  - analysis
  - persistence

- Delete-friendly structure

### Operational Safety

- Admin-only access is enforced server-side
- Crawl runs can be deleted cleanly
- Failures are logged with context

### Developer Experience

- Repo intent is obvious from docs
- Setup steps are minimal
- No hidden “magic”

---

## Acceptance Tests (Human-Level)

- You can run the tool on a site and quickly understand it
- You can explain _why_ an issue was flagged
- You can confidently say what to fix first
- You can rerun later and compare results
- A future you can open the repo and understand it in 15 minutes

---
