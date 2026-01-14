---

# 📐 SCOPE_AND_PHASES.md

## Scope Philosophy

This project is built under **constraint-first development**:

> We remove aggressively first, then build back only what serves the core outcome.

---

## Feature Whitelist (v1)

Only features on this list are allowed:

- Admin-only authentication
- Content-first crawling
- Page inventory with extracted text
- Lightweight importance heuristics
- Obvious issue detection
- Persistent crawl history
- Simple admin UI for inspection
- Logging and failure visibility

---

## Feature Blacklist (v1)

Explicitly forbidden in v1:

- Selector-based scraping
- User-defined scraping rules
- Client-facing reports
- Export formats (PDF, CSV, etc.)
- Billing or usage tracking
- Advanced permissions
- AI-driven “SEO scoring”
- WebSockets or real-time dashboards

If a feature is not on the whitelist, it does not get built.

---

## Phase Plan

### Phase 0 — Cleanup & Alignment (Required)

**Goal:** Remove ambiguity and dead weight.

Tasks:

- Remove unused packages and services
- Delete or isolate:

  - selector-based scraping
  - unused API routers
  - unused workers

- Align docs with reality
- Ensure repo matches the PRD intent

Exit criteria:

- No unused routes
- No unreachable code
- Docs reflect actual behavior

---

### Phase 1 — Minimal Credible Core

**Goal:** Deliver the smallest useful version.

Tasks:

- Content-first crawl pipeline
- Page inventory persistence
- Basic issue detection
- Admin-only access
- Crawl history metadata
- Minimal UI for inspection

Exit criteria:

- You can run it weekly and get value

---

### Phase 2 — Insight Refinement (Optional)

- Better prioritization heuristics
- Comparative analysis (runs vs runs)
- Optional AI summaries (opt-in)

---

### Phase 3 — Productization (Future)

- Client reports
- Exports
- Multi-user access
- SaaS concerns

Only considered if Phase 1 proves valuable.

---

## Final Note (Important)

This project succeeds **not by adding features**, but by:

- Making fewer assumptions
- Producing clearer signal
- Supporting better decisions

Deletion is progress.

---

Great question — and this is exactly the right moment to do this transformation.

What you pasted is a **platform scaffold milestone plan** (CushLabs Base).
What you now need is a **product-specific milestone plan** for your **internal, content-first site analysis tool**.

We are **not throwing this away**.
We are **re-anchoring it to intent**.

Below is a **clean, relevant rewrite** that:

- Keeps the _discipline_ of the original plan
- Adds the **Phase 0 cleanup you explicitly want**
- Removes SaaS scaffolding milestones that no longer matter
- Aligns milestones with **outcomes**, not infrastructure for its own sake

---

# 🗺️ MILESTONE_PLAN.md

**Project:** CushLabs Site Analysis (Internal Tool)

Milestones are scoped to **protect clarity, signal, and usefulness**.

Each milestone is defined by:

- Goal
- Acceptance criteria
- Primary areas affected

This plan assumes:

- Single operator
- Admin-only access
- Content-first crawling
- No public SaaS concerns in v1

---

## Milestone 0 — Intent Alignment & Cleanup (Required)

### Goal

Remove ambiguity, dead code, and unused capabilities so the repo reflects the **actual intent** of the tool.

This milestone is about **deletion**, not building.

### Acceptance Criteria

- Selector-based scraping code is removed or isolated
- Unmounted or unused API routers are deleted
- Duplicate or conflicting worker implementations are resolved
- Docs that describe non-existent behavior are corrected or removed
- Dependencies not required for v1 intent are removed
- Repo can be explained as:

  > “An internal site analysis tool”

### Primary Areas Affected

- Backend scraping/task code
- Worker configuration
- API routing
- `docs/`
- `package.json` / `requirements.txt`

---

## Milestone 1 — Admin-Only Access & Safety Baseline

### Goal

Ensure the tool is explicitly **internal and admin-only**, with no accidental exposure.

### Acceptance Criteria

- Authentication is required to access any functionality
- All routes are protected server-side
- No unauthenticated crawl execution is possible
- Admin status is enforced consistently
- No client-side checks alone gate sensitive actions

### Primary Areas Affected

- Auth middleware
- Backend auth enforcement
- Admin UI boundaries
- Documentation of access assumptions

---

## Milestone 2 — Content-First Crawling Core

### Goal

Establish a reliable crawl pipeline whose **primary output is analyzable content**.

### Acceptance Criteria

- A crawl can be initiated for a target site
- Pages are fetched up to defined limits (depth/page count)
- Clean text content is extracted for each page
- Each page record includes:

  - URL
  - status code
  - title / H1 (if present)
  - word count
  - extracted text

- Crawl failures are logged and visible

### Primary Areas Affected

- Crawl engine
- Content extraction logic
- Persistence layer (pages, crawls)
- Storage conventions

---

## Milestone 3 — Page Inventory & Structural Understanding

### Goal

Make the site **understandable at a glance**.

### Acceptance Criteria

- Page inventory can be listed per crawl
- Pages can be sorted / filtered by:

  - importance heuristics
  - status
  - content size

- Simple importance signals exist (e.g. link count, depth)
- Operator can answer:

  > “What pages exist and which ones matter?”

### Primary Areas Affected

- Page models
- Inventory queries
- Admin UI inspection views

---

## Milestone 4 — Obvious Issue Detection (High-Signal Only)

### Goal

Surface **real, defensible problems** without noise.

### Acceptance Criteria

- Tool flags:

  - missing or junk titles
  - extremely thin pages
  - broken pages expected to work
  - unintentionally non-indexable pages

- Each issue includes:

  - why it was flagged
  - which pages are affected

- No academic or speculative SEO metrics

### Primary Areas Affected

- Analysis logic
- Issue models
- Issue presentation in UI

---

## Milestone 5 — Prioritization & Opportunity Framing

### Goal

Help the operator decide **what to fix first**.

### Acceptance Criteria

- Issues are grouped by impact
- Operator can see:

  - which issues affect important pages
  - which fixes would move the needle fastest

- Output supports:

  > “If I only fix 3 things, what should they be?”

Rule-based prioritization is acceptable in v1.

### Primary Areas Affected

- Analysis aggregation
- Summary views
- Insight framing

---

## Milestone 6 — Evidence & Run History

### Goal

Ensure results are **durable and comparable**.

### Acceptance Criteria

- Crawl runs are stored with timestamps and config
- Extracted content is persisted per run
- Operator can review past runs
- Optional:

  - raw HTML snapshots stored for verification/debugging

Crawl history is treated as **metadata**, not a feature.

### Primary Areas Affected

- Storage
- Crawl metadata
- Admin inspection views

---

## Milestone 7 — Docs & Scope Freeze

### Goal

Make the project understandable, defensible, and reusable **without tribal knowledge**.

### Acceptance Criteria

- PRD reflects actual behavior
- Scope boundaries are explicit
- Whitelist / blacklist is enforced
- Repo can be re-opened in 6 months and understood quickly
- “Why this exists” is clear from docs alone

### Primary Areas Affected

- `docs/PROJECT_BRIEF.md`
- `docs/PRD.md`
- `docs/SCOPE_BOUNDARIES.md`
- `docs/ARCHITECTURE_INTENT.md`
- `docs/INDEX.md`

---

## Definition of v1 “Done”

v1 is complete when:

- You can run it weekly on a real site
- You get real insight, not noise
- You trust the output
- You know what to fix first
- You don’t feel tempted to add features “just because”

---

## Final Note (Intent Lock)

This project succeeds by:

- Reducing ambiguity
- Favoring clarity over coverage
- Supporting judgment, not replacing it

Deletion is progress.
Insight is the product.

---
