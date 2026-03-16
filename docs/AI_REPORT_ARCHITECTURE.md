# AI Report Architecture

> How the AI-powered site audit report works, and the design decisions behind it.

---

## Two-Stage Pipeline: Python Analyzes, AI Narrates

The report is generated in two distinct phases:

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

### Stage 2: AI Narrative (LLM)

The LLM receives the **pre-computed findings** and tells the story behind the numbers.

**What it receives:**
- Summary scorecard (avg score, pass rates, distribution)
- All specific findings as structured text
- Per-page scores with issue summaries

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
   - Critical Issues (with affected URLs)
   - Quick Wins (copy-paste fixes)
   - Strategic Recommendations (with effort estimates)
   - Strengths & Weaknesses
   - Action Plan

---

## File Locations

| Component | File | Purpose |
|-----------|------|---------|
| Report endpoint | `backend/app/api/routes/analysis.py` | Data collection, Python analysis, LLM call, report assembly |
| LLM prompt | `backend/app/services/llm_service.py` | `generate_executive_summary()` — narrator prompt |
| Pydantic models | `backend/app/models/llm_models.py` | `ExecutiveSummary`, `CriticalIssue`, `StrategicRecommendation` |
| Frontend rendering | `frontend/src/pages/CrawlDetailPage.tsx` | Report tab UI with data tables and AI narrative |
| TypeScript types | `frontend/src/services/api.ts` | `CrawlReport` interface with data_findings, page_audits, summary_stats |

---

## Current Limitations & Future Improvements

### What works well
- Python-computed findings are always specific and data-grounded
- Pass rate scorecard gives instant visibility into SEO health
- Page audit table lets you see every page's status at a glance
- AI narrative connects dots between individual findings

### Potential improvements
- **Content snippets**: Include actual title/meta text in the findings table so users can see what needs changing without clicking through
- **Trend tracking**: Compare current audit to previous audits (requires storing historical reports)
- **Fix suggestions**: Have the AI suggest specific replacement titles/metas based on the page content
- **Severity weighting**: Weight findings by page importance (homepage issues > deep blog post issues)
- **Export**: PDF/CSV export of the full report for client delivery

---

*Last updated: March 15, 2026*
