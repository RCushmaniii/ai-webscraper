# Issue Detection System - Specification

## Overview

The current Issues tab is not providing value because issue detection is too basic. This document outlines a comprehensive, actionable issue detection system that provides real value to clients.

## Problem Statement

**Current State:**

- Generic checks (missing title, meta description)
- Most modern websites pass these basic checks
- Result: Empty Issues tab with no actionable insights

**What Clients Actually Need:**

- Broken links and resources (direct UX impact)
- Performance bottlenecks (Core Web Vitals)
- Accessibility violations (legal compliance)
- SEO competitive gaps (ranking opportunities)
- Conversion blockers (revenue impact)
- Content quality issues (engagement)

---

## Issue Categories & Detection Logic

### 1. **Broken Links & Resources** (Critical Priority)

**Why It Matters:** Direct negative impact on UX and SEO. Easy to fix, high ROI.

#### Issues to Detect:

| Issue                   | Detection Logic                               | Severity | Fix Suggestion                               |
| ----------------------- | --------------------------------------------- | -------- | -------------------------------------------- |
| Internal 404 errors     | `status_code == 404 AND is_internal == true`  | Critical | Update or remove broken internal links       |
| Broken images           | `status_code == 404 AND type == 'image'`      | High     | Replace or remove broken images              |
| External link errors    | `status_code >= 400 AND is_internal == false` | Medium   | Update or remove broken external links       |
| Redirect chains         | `status_code == 301 → 301 → 200` (3+ hops)    | Medium   | Update links to final destination            |
| Slow external resources | `latency_ms > 5000`                           | Low      | Consider removing slow third-party resources |

**Data Already Available:** ✅ Yes (links table has status_code, is_internal, latency_ms)

---

### 2. **Performance Issues** (High Priority)

**Why It Matters:** Google Core Web Vitals ranking factor. User retention (53% abandon if load > 3s).

#### Issues to Detect:

| Issue                     | Detection Logic         | Severity | Fix Suggestion                           |
| ------------------------- | ----------------------- | -------- | ---------------------------------------- |
| Large page size           | `page_size_bytes > 3MB` | High     | Optimize images, minify CSS/JS           |
| Unoptimized images        | `image_size > 500KB`    | High     | Compress images, use WebP format         |
| Too many external scripts | `external_scripts > 10` | Medium   | Reduce third-party dependencies          |
| Missing image dimensions  | `!width OR !height`     | Medium   | Add width/height to prevent layout shift |
| Large DOM size            | `dom_elements > 1500`   | Low      | Simplify page structure                  |

**Data Needed:**

- ✅ `page_size_bytes` (already in pages table)
- ✅ `image.size` (already in images table)
- ❌ Script count (need to extract)
- ❌ DOM element count (need to extract)

---

### 3. **Mobile & Accessibility** (High Priority)

**Why It Matters:** Legal compliance (ADA/WCAG), 60%+ mobile traffic, inclusive design.

#### Issues to Detect:

| Issue                      | Detection Logic                                | Severity | Fix Suggestion                             |
| -------------------------- | ---------------------------------------------- | -------- | ------------------------------------------ |
| Missing viewport meta      | `!has_viewport_meta`                           | Critical | Add `<meta name="viewport">` tag           |
| Images missing alt text    | `!alt_text`                                    | High     | Add descriptive alt text for accessibility |
| Low color contrast         | Contrast ratio < 4.5:1 (WCAG AA)               | High     | Increase text/background contrast          |
| Form inputs without labels | `<input>` without associated `<label>`         | High     | Add labels to all form inputs              |
| Non-descriptive link text  | Link text == "click here", "read more", "here" | Medium   | Use descriptive link text                  |
| Small text                 | Font size < 16px on body text                  | Medium   | Increase font size for readability         |
| Small touch targets        | Button/link < 48x48px                          | Medium   | Increase touch target size                 |

**Data Needed:**

- ✅ `has_viewport_meta` (already extracted)
- ✅ `alt_text` (already in images table)
- ❌ Color contrast (need to analyze CSS)
- ❌ Form labels (need to extract)
- ❌ Link text analysis (need to extract)
- ❌ Font sizes (need to extract)

---

### 4. **SEO Competitive Gaps** (High Priority)

**Why It Matters:** Ranking improvements, traffic growth, competitive advantage.

#### Issues to Detect:

| Issue                       | Detection Logic                                  | Severity | Fix Suggestion                              |
| --------------------------- | ------------------------------------------------ | -------- | ------------------------------------------- |
| Missing schema markup       | No JSON-LD or microdata found                    | High     | Add structured data (Product, Article, FAQ) |
| No Open Graph tags          | Missing `og:title`, `og:description`, `og:image` | High     | Add OG tags for better social sharing       |
| Missing canonical tag       | No `<link rel="canonical">`                      | High     | Add canonical to prevent duplicate content  |
| Duplicate titles            | Same title on multiple pages                     | High     | Create unique titles for each page          |
| Duplicate meta descriptions | Same description on multiple pages               | Medium   | Write unique descriptions                   |
| Thin content                | `word_count < 300` on non-nav pages              | Medium   | Expand content to 500+ words                |
| No internal links           | Page has 0 internal links pointing to it         | Medium   | Add internal links from related pages       |
| Missing robots meta         | No robots meta tag                               | Low      | Add robots meta for crawl control           |

**Data Needed:**

- ❌ Schema markup detection (need to extract JSON-LD)
- ❌ Open Graph tags (need to extract)
- ❌ Canonical tags (need to extract)
- ✅ Title/description (already in seo_metadata table)
- ✅ Word count (already in pages table)
- ✅ Internal link count (can query links table)

---

### 5. **Conversion Optimization** (Medium Priority)

**Why It Matters:** Direct revenue impact, lead generation, user engagement.

#### Issues to Detect:

| Issue                  | Detection Logic                     | Severity | Fix Suggestion                       |
| ---------------------- | ----------------------------------- | -------- | ------------------------------------ |
| No CTA above fold      | No button/link in first 800px       | High     | Add clear call-to-action above fold  |
| Long forms             | Form with > 5 input fields          | Medium   | Reduce form fields or use multi-step |
| No trust signals       | No testimonials, reviews, or badges | Medium   | Add social proof elements            |
| Missing contact info   | No phone/email/address visible      | Medium   | Add contact information              |
| No privacy policy link | No link to privacy policy           | Low      | Add privacy policy link in footer    |

**Data Needed:**

- ❌ CTA detection (need to analyze buttons/links above fold)
- ❌ Form field count (need to extract)
- ❌ Trust signal detection (need to analyze content)
- ❌ Contact info detection (need to analyze content)
- ❌ Privacy policy link (need to check footer links)

---

### 6. **Content Quality** (Medium Priority)

**Why It Matters:** User engagement, time on site, bounce rate, search rankings.

#### Issues to Detect:

| Issue                    | Detection Logic                   | Severity | Fix Suggestion                             |
| ------------------------ | --------------------------------- | -------- | ------------------------------------------ |
| Duplicate content        | Content hash matches another page | High     | Rewrite or consolidate duplicate pages     |
| Keyword stuffing         | Keyword density > 3%              | High     | Reduce keyword repetition, write naturally |
| Poor readability         | Flesch Reading Ease < 60          | Medium   | Simplify language, shorter sentences       |
| Orphan pages             | 0 internal links pointing to page | Medium   | Add internal links from related pages      |
| Missing H1               | No H1 tag found                   | Medium   | Add descriptive H1 heading                 |
| Multiple H1s             | More than 1 H1 tag                | Medium   | Use only one H1 per page                   |
| Broken heading hierarchy | H1 → H3 (skips H2)                | Low      | Fix heading hierarchy (H1→H2→H3)           |

**Data Needed:**

- ✅ Content hash (already in pages table)
- ❌ Keyword density (need to analyze)
- ❌ Readability score (need to calculate Flesch)
- ✅ Internal links (can query links table)
- ✅ H1 count (already extracted)
- ✅ Heading hierarchy (already extracted)

---

### 7. **Security & Trust** (Medium Priority)

**Why It Matters:** User trust, data protection, Google ranking factor.

#### Issues to Detect:

| Issue                           | Detection Logic                            | Severity | Fix Suggestion                |
| ------------------------------- | ------------------------------------------ | -------- | ----------------------------- |
| Mixed content                   | HTTPS page loading HTTP resources          | Critical | Update all resources to HTTPS |
| External links without noopener | `target="_blank"` without `rel="noopener"` | Medium   | Add rel="noopener noreferrer" |
| Forms without HTTPS             | Form action uses HTTP                      | High     | Use HTTPS for all forms       |
| Missing security headers        | No CSP, X-Frame-Options, etc.              | Low      | Add security headers          |

**Data Needed:**

- ❌ Mixed content detection (need to analyze resource URLs)
- ❌ Link rel attributes (need to extract)
- ❌ Form action URLs (need to extract)
- ❌ Security headers (need to check HTTP response)

---

## Implementation Phases

### **Phase 1: Quick Wins** (Use Existing Data)

**Timeline:** 1-2 days

Implement issues that use data we already have:

1. ✅ Broken internal links (404s)
2. ✅ Broken images
3. ✅ Large page sizes (> 3MB)
4. ✅ Unoptimized images (> 500KB)
5. ✅ Images missing alt text
6. ✅ Duplicate titles/descriptions
7. ✅ Thin content (< 300 words)
8. ✅ Orphan pages (no internal links)
9. ✅ Missing H1 / Multiple H1s
10. ✅ Heading hierarchy issues

**Impact:** Immediate value, 10+ actionable issues per crawl

---

### **Phase 2: Enhanced Extraction** (Add New Data Collection)

**Timeline:** 3-4 days

Enhance crawler to extract additional data:

1. Schema markup (JSON-LD)
2. Open Graph tags
3. Canonical tags
4. Form analysis (field count, labels)
5. CTA detection (buttons above fold)
6. Link rel attributes
7. Script/stylesheet counts

**Impact:** 15+ additional issue types

---

### **Phase 3: Advanced Analysis** (AI-Powered)

**Timeline:** 5-7 days

Use AI for complex analysis:

1. Readability scoring (Flesch-Kincaid)
2. Keyword density analysis
3. Content quality assessment
4. Trust signal detection
5. Color contrast checking
6. Duplicate content detection (semantic, not just hash)

**Impact:** Premium feature for Pro/Enterprise tiers

---

## Database Schema Updates

```sql
-- Add columns to pages table for new metrics
ALTER TABLE pages ADD COLUMN has_schema_markup BOOLEAN DEFAULT false;
ALTER TABLE pages ADD COLUMN has_open_graph BOOLEAN DEFAULT false;
ALTER TABLE pages ADD COLUMN has_canonical BOOLEAN DEFAULT false;
ALTER TABLE pages ADD COLUMN readability_score NUMERIC(5,2);
ALTER TABLE pages ADD COLUMN keyword_density NUMERIC(5,2);
ALTER TABLE pages ADD COLUMN has_cta_above_fold BOOLEAN DEFAULT false;
ALTER TABLE pages ADD COLUMN form_field_count INTEGER DEFAULT 0;
ALTER TABLE pages ADD COLUMN external_script_count INTEGER DEFAULT 0;
ALTER TABLE pages ADD COLUMN dom_element_count INTEGER DEFAULT 0;

-- Add indexes for issue queries
CREATE INDEX idx_pages_broken_links ON pages(crawl_id) WHERE status_code >= 400;
CREATE INDEX idx_pages_large_size ON pages(crawl_id) WHERE page_size_bytes > 3145728; -- 3MB
CREATE INDEX idx_pages_thin_content ON pages(crawl_id) WHERE word_count < 300;
```

---

## UI Enhancements

### Issues Tab Redesign

**Current:** Flat list of issues

**Proposed:** Categorized, filterable, actionable

```
┌─────────────────────────────────────────────────────┐
│  Issues (47)                    [Filter ▼] [Export] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔴 Critical (8)                                     │
│  ├─ Broken Links (5)                                │
│  │   • /about → 404 Not Found                       │
│  │   • /contact → 404 Not Found                     │
│  │   └─ [Fix: Update or remove links]               │
│  │                                                   │
│  └─ Missing Viewport Meta (3 pages)                 │
│      • Homepage, Services, Contact                  │
│      └─ [Fix: Add viewport meta tag]                │
│                                                      │
│  🟡 High (15)                                        │
│  ├─ Images Missing Alt Text (12)                    │
│  │   • logo.png, hero-image.jpg, ...               │
│  │   └─ [Fix: Add descriptive alt text]            │
│  │                                                   │
│  └─ No Schema Markup (3 pages)                      │
│      • Product pages missing Product schema         │
│      └─ [Fix: Add JSON-LD structured data]         │
│                                                      │
│  🟠 Medium (18)                                      │
│  └─ Thin Content (18 pages)                         │
│      • Pages with < 300 words                       │
│      └─ [Fix: Expand content to 500+ words]        │
│                                                      │
│  🔵 Low (6)                                          │
│  └─ Large Page Size (6 pages)                       │
│      • Pages > 3MB                                  │
│      └─ [Fix: Optimize images and assets]          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Features:**

- Grouped by severity (Critical, High, Medium, Low)
- Grouped by category (Broken Links, SEO, Performance, etc.)
- Click to expand and see affected pages
- Fix suggestions for each issue type
- Export issues as CSV/PDF for client reports
- Filter by category, severity, page type

---

## Success Metrics

**Before:**

- Average issues per crawl: 0-2
- Client value: Low (generic SEO checks)

**After Phase 1:**

- Average issues per crawl: 15-30
- Client value: High (actionable, specific fixes)

**After Phase 2:**

- Average issues per crawl: 30-50
- Client value: Very High (comprehensive audit)

**After Phase 3:**

- Average issues per crawl: 50-100
- Client value: Premium (AI-powered insights)

---

## Competitive Advantage

Most web crawlers focus on technical SEO. This system provides:

1. **Conversion optimization** insights (unique)
2. **Accessibility compliance** (legal requirement)
3. **Performance optimization** (Core Web Vitals)
4. **Actionable fix suggestions** (not just detection)
5. **Categorized, prioritized** issues (easy to act on)

This positions the tool as a **comprehensive website audit platform**, not just a crawler.
