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
