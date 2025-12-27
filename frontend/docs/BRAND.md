# BRAND.md - CushLabs.ai Design & Strategy System

## 1. Brand Identity & Positioning

**Product Name:** AI Web Scraper | _by CushLabs.ai_
**Tagline:** Crawl. Inspect. Prioritize.
**Elevator Pitch:** An internal site analysis workspace that surfaces high-signal issues so you can prioritize what to fix next, without the noise of generic SEO scores.

### Core Value Proposition

- **Trustworthy:** Predictable, transparent, and respectful of crawling limits.
- **Operational:** Focused on actions (fixing issues), not vanity metrics.
- **Plush:** A high-comfort UI with generous whitespace that reduces cognitive load.

### Voice & Tone

- **The Vibe:** "A calm internal tool that tells you what it did, what it found, and what to do next."
- **Attributes:** Professional but Personal. Experienced but not "Old School."
- **Inspirations:** Stripe (Clarity), Linear (Focus), Vercel (Technical Elegance).

---

## 2. Visual Design System (The "Plush" Look)

_A sophisticated "Deep Slate & Orange" theme. This replaces harsh contrasts with a calming, professional palette that feels expensive and reduces eye strain._

### Color Palette

| Usage                          | Color Name       | Hex Code  | Tailwind Equivalent |
| :----------------------------- | :--------------- | :-------- | :------------------ |
| **Brand Primary** (Header/Nav) | **Deep Slate**   | `#1E293B` | `slate-800`         |
| **Primary Action** (Buttons)   | **Warm Orange**  | `#F97316` | `orange-500`        |
| **Action Hover**               | **Deep Orange**  | `#EA580C` | `orange-600`        |
| **App Background**             | **Pale Cloud**   | `#F8FAFC` | `slate-50`          |
| **Content Panels**             | **Pure White**   | `#FFFFFF` | `white`             |
| **Primary Text**               | **Charcoal**     | `#1F2937` | `gray-800`          |
| **Secondary Text**             | **Steel Gray**   | `#64748B` | `slate-500`         |
| **Status: Error**              | **Soft Red**     | `#EF4444` | `red-500`           |
| **Status: Success**            | **Emerald**      | `#10B981` | `emerald-500`       |

### Typography

- **Font Family:** `Inter`, `Roboto`, or `Open Sans` (Geometric Sans-serif).
- **Headings:** Semi-Bold (600). Deep Slate.
- **Body:** Regular (400). Charcoal. Line-height 1.6 for readability.

### Layout & Spacing Rules

- **"Plush" Padding:**
  - **Containers:** `4rem` (64px) padding on desktop.
  - **Cards:** `2.5rem` (40px) internal padding.
  - **Buttons:** `12px` Vertical x `24px` Horizontal.
- **Max Width:** `1200px` centered container (prevents eye-scanning fatigue).
- **Corner Radius:** `12px` (Soft, modern corners).
- **Shadows:** Soft, diffused shadows for elevation.

---

## 3. UI Copy & Language

### English Guidelines (Default)

- **Do:** Use active, concrete verbs ("Start Crawl", "View Pages").
- **Don't:** Use vague jargon ("Execute", "Process", "Anomaly").
- **Error Messages:** Must state _what_ happened and _what_ to do next.
  - _Bad:_ "Connection Failed."
  - _Good:_ "Supabase is unreachable. Verify your API keys and try again."

### Spanish Localization (PyME Focused)

_Context: Professional, direct, and accessible for SMB owners._

| English Term    | Spanish Translation |
| :-------------- | :------------------ |
| **Crawl**       | Rastreo / Rastrear  |
| **Start Crawl** | Iniciar rastreo     |
| **Pages**       | Páginas             |
| **Links**       | Enlaces             |
| **Issues**      | Problemas           |
| **Rate Limit**  | Límite de velocidad |
| **Settings**    | Configuración       |

---

## 4. Components & UX Patterns

### The "Empty State" Pattern (Priority UX)

_Solving the "Redundant Button" issue._

1.  **When List is Empty:**
    - **Top Right Button:** Hidden or Disabled.
    - **Center Hero:** A large, padded white panel.
    - **Illustration:** A friendly, grayed-out icon (folder/robot).
    - **Text:** "No crawls found. Start your first site analysis."
    - **Primary Action:** Large Orange Button: "Create First Crawl".
2.  **When List has Data:**
    - **Top Right Button:** Visible (Primary "New Crawl").
    - **Center Area:** Displays Data Table of previous runs.

### Navigation Bar

- **Background:** Deep Slate (`#1E293B`).
- **Height:** `80px`.
- **Left:** "AI WebScraper" (Bold White) | "by CushLabs.ai" (Light Gray).
- **Right:** Navigation Links + "Sign Out" (Ghost button style).
