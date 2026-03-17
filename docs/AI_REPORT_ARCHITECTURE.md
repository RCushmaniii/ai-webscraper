# AI Report Architecture

> How the AI-powered site audit report works, and the design decisions behind it.

---

## Three-Stage Pipeline: Python Analyzes, Python Extracts, AI Narrates + Evaluates

The report is generated in three distinct phases:

### Stage 1: Data Analysis (Python)

Python computes **all quantitative findings** directly from the crawl data. No LLM involved.

**What it produces:**

1. **Per-Page Audit** — Every page graded on 6 dimensions:
   - Title tag: pass (30-60 chars), fail (too short/long), or missing
   - Meta description: pass (120-160 chars), fail, or missing
   - H1 tag: present or missing
   - Content depth: pass (300+ words), thin, or empty
   - Response time: pass (<1s), slow (1-3s), or critical (>3s)
   - Status code: pass (2xx/3xx) or fail (4xx/5xx)

2. **Page Score** (0-100) — Weighted penalties per dimension:
   - Missing title: -25 | Bad title length: -10
   - Missing meta: -20 | Bad meta length: -8
   - Missing H1: -15
   - Thin content: -10 | Empty content: -20
   - Slow response: -5 | Critical response: -15
   - HTTP error: -25

3. **Summary Stats** — Aggregate pass rates:
   - Title pass rate, Meta pass rate, H1 pass rate, Content pass rate, Speed pass rate
   - Pages passing/warning/failing distribution

4. **Specific Findings** — Individual issues with:
   - Category (SEO, Content, Performance, Links, Accessibility)
   - Severity (high/medium/low)
   - Finding text with actual URL, current value, and target
   - Example: `"Title too short on /services: 'CushLabs Services' (23 chars), target 30-60"`

### Stage 2: Semantic Skeleton Extraction (Python → AI)

For top pages (primary/high nav_score, max 10), Python extracts structural signals from stored HTML snapshots, then the AI evaluates messaging quality.

**Python extracts (no LLM):**
- H1, H2 headings
- First sentence of each paragraph (messaging flow)
- CTA button text (`<button>` + `<a>` with button classes)
- Page purpose inferred from URL patterns (e.g., `/contact` → lead_generation, `/blog` → educational)
- Page language from `<html lang="...">`

**AI evaluates (gpt-4o-mini, ~$0.004 per report):**
- **Intent Gap Analysis** — Does messaging match the page's purpose?
- **Tone & Persona Audit** — Does tone fit the audience?
- **Skim Test** — Do headings tell a story when skimmed?
- **Overall Strategy Score** (0-100) + top recommendation
- Optional suggested title/meta rewrites (Python-validated for length)

**Key files:**
- `backend/app/services/semantic_builder.py` — Pure Python skeleton extraction
- `backend/app/services/llm_service.py` → `analyze_page_strategy()` — CRO-specific LLM prompt
- `backend/app/models/llm_models.py` — `PageSemanticStrategy`, `IntentGapAnalysis`, `TonePersonaAudit`, `SkimTestAudit`

**Design decisions:**
- Uses gpt-4o-mini (not 4o) — skeleton is compact, task is well-constrained, 16x cheaper
- LLM calls run in parallel via `asyncio.gather(return_exceptions=True)` — one failure doesn't block others
- Suggested titles/metas are Python-validated (title 20-80 chars, meta 100-200 chars) — bad suggestions are nulled out
- Legal pages (`/privacy`, `/terms`) are skipped — no point critiquing a privacy policy's "conversion strategy"
- Entire phase wrapped in try/except — graceful degradation if HTML snapshots unavailable

### Stage 3: AI Narrative (LLM)

The LLM receives the **pre-computed findings** AND **strategy analysis results**, then tells the story behind the numbers.

**What it receives:**
- Summary scorecard (avg score, pass rates, distribution)
- All specific findings as structured text
- Per-page scores with issue summaries
- Strategy findings summary (avg strategy score, per-page intent/tone/skim scores, top recommendations)

**What it produces (via structured Pydantic output):**
- Site health score (0-100)
- Sub-scores: Technical SEO, Content Quality, UX, Trust Signals
- Critical issues with affected URLs and recommended actions
- Quick wins (copy-paste fixes)
- Strategic recommendations with effort estimates
- Strengths and weaknesses narratives
- Action plan summary

**Key design principle:** The AI never invents data. It narrates patterns, explains business implications, and prioritizes actions based on the data Python already computed. If the data says "5 pages have meta descriptions at 167 chars," the AI might say: "All five pages overshoot by exactly 7 characters — this looks like a template issue. One config change fixes all five."

---

## How AI Is Leveraged

This is not a simple "send data to GPT and get a report" approach. The architecture is specifically designed to avoid generic AI output:

1. **Separation of concerns** — Python handles facts, AI handles interpretation. This prevents the LLM from hallucinating statistics or making vague claims.

2. **Structured output** — The LLM response is forced into a Pydantic schema via the `instructor` library. Every field has a description that guides the AI toward specificity. For example, `quick_wins` is described as "Specific copy-paste fixes citing URLs and values."

3. **Banned phrases** — The system prompt explicitly bans consultant-speak: "conduct regular site audits", "implement SEO strategy", "optimize SEO elements", etc. These phrases instantly kill credibility.

4. **Data grounding** — Every finding the AI references must trace back to a specific data point. The prompt says: "If a finding says 'Meta description too long on /services: 167 chars' then your recommendation must say '/services' and '167 chars'."

5. **Role framing** — The system prompt positions the AI as a narrator, not an analyst: "You narrate data — you don't generate it." This keeps it from inventing insights that aren't supported by the crawl data.

---

## Report Sections in the Frontend

The report renders in this order:

1. **Site Health Score** — Big number (0-100) with one-line AI summary
2. **Score Breakdown** — 4 sub-scores (Technical SEO, Content, UX, Trust)
3. **Crawl Metrics** — Pages crawled, total issues, broken links, missing meta
4. **SEO Pass Rates** — 5 dimensions with % pass rates (Python-computed)
5. **Specific Findings Table** — Severity, category, finding, current value, target (Python-computed)
6. **Page-by-Page Audit Table** — Every page with pass/fail checkmarks and score (Python-computed)
7. **"Behind the Numbers" AI Narrative:**
   - **Strategy & Conversion Analysis** — Per-page collapsible cards with purpose badge, 3 sub-scores (intent/tone/skim), top recommendation, expandable gaps/suggestions, suggested title/meta fixes
   - Critical Issues (with affected URLs)
   - Quick Wins (copy-paste fixes)
   - Strategic Recommendations (with effort estimates)
   - Strengths & Weaknesses
   - Action Plan

---

## File Locations

| Component | File | Purpose |
|-----------|------|---------|
| Report endpoint | `backend/app/api/routes/analysis.py` | Data collection, Python analysis, Phase 3.5 strategy, LLM call, report assembly |
| Semantic builder | `backend/app/services/semantic_builder.py` | Pure Python: extract headings, CTAs, infer purpose, build skeleton |
| LLM service | `backend/app/services/llm_service.py` | `generate_executive_summary()` + `analyze_page_strategy()` |
| Pydantic models | `backend/app/models/llm_models.py` | `ExecutiveSummary`, `PageSemanticStrategy`, `IntentGapAnalysis`, etc. |
| LLM config | `backend/app/core/llm_config.py` | `SEMANTIC_STRATEGY` task config (gpt-4o-mini, 600 tokens, tier 2) |
| Frontend rendering | `frontend/src/pages/CrawlDetailPage.tsx` | Report tab UI with data tables, strategy cards, and AI narrative |
| TypeScript types | `frontend/src/services/api.ts` | `CrawlReport` interface with data_findings, page_audits, semantic_strategy |

---

## Current Limitations & Future Improvements

### What works well
- Python-computed findings are always specific and data-grounded
- Pass rate scorecard gives instant visibility into SEO health
- Page audit table lets you see every page's status at a glance
- AI narrative connects dots between individual findings
- Semantic strategy analysis provides CRO insights no other crawler tool offers
- Purpose inference correctly identifies page types from URL patterns
- Strategy section gracefully degrades if HTML snapshots unavailable

### Potential improvements
- **Persistent HTML storage**: Move HTML snapshots to Supabase Storage or S3 (currently ephemeral on Render free tier — snapshots lost on redeploy)
- **Trend tracking**: Compare current audit to previous audits (requires storing historical reports)
- **Severity weighting**: Weight findings by page importance (homepage issues > deep blog post issues)
- **Export**: PDF/CSV export of the full report for client delivery

### Known gotcha: HTML column name
The pages table has `html_storage_path` (migration name). The crawler was historically writing `html_snapshot_path`. As of March 2026, the crawler writes `html_storage_path` and the report queries both names for backwards compatibility.

---

*Last updated: March 16, 2026*
