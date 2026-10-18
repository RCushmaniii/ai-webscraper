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

## 2. Visual Design System

> **Superseded 2026-10-18.** Color and type now come from the CushLabs brand kit
> (`operating-system/cushlabs/brand-kit.md`; canonical source `cushlabs/src/styles/global.css`).
> The "Deep Slate & Orange" palette that used to live here is retired. If this section and the
> kit disagree, the kit wins.

### Values as implemented (`frontend/tailwind.config.cjs`)

| Role | Class scale | Value | Notes |
| :--- | :---------- | :---- | :---- |
| **Accent** (buttons, rings, emphasis) | `secondary-500` | `#FF6A3D` | The one accent. `secondary-600` `#FD4C00` for hover. |
| Accent text on white (AA) | `secondary-700` | `#BA4D2D` | Use for small orange type; 500/600 are for fills. |
| Header / footer field | `primary-900` | `#0A0A0A` | Near-black. `primary-950` is pure black. |
| Surfaces on dark | `primary-800/700/600` | `#141414` / `#1A1A1A` / `#2A2A2A` | |
| Sub-copy greys | `primary-500/400/300` | `#666666` / `#888888` / `#AAAAAA` | |
| Type on light | `neutral-charcoal` | `#111111` | |
| App background | `neutral-cloud` | `#F7F7F7` | Neutral, not blue-tinted. |
| Status | `success-*`, `error-*` | emerald / red | Unchanged. |

`primary-*` is the **neutral** scale and `secondary-*` is the **accent** scale. The names are
historical - every page already used them - so the values were swapped underneath. Do not add a
blue, purple or teal accent anywhere; teal in particular was retired fleet-wide in July 2026.

### Typography

- **Display - Manrope 700** (`font-display`): headings, the wordmark line, buttons, big numbers.
  `h1`-`h4` get it globally in `src/index.css`.
- **Body - Inter 400** (`font-sans`): everything that is read.
- Both are self-hosted from `public/fonts/` (same files as cushlabs.ai) so the Caddy CSP stays at
  `font-src 'self'`.
- Sentence case for headings.

### The mark

The chevron-C (`public/favicon.svg` on light, `public/cushlabs-mark-on-dark.svg` on dark). Masters
and rules: `operating-system/cushlabs/brand-mark.md`. Never redraw it, never below 32px, bump the
`?v=N` on the favicon links when the artwork changes.

### Layout & Spacing Rules (unchanged)

- **Containers:** `4rem` (64px) padding on desktop. **Cards:** `2.5rem` (40px).
- **Max width:** `1200px` centered container.
- **Corner radius:** `12px`. **Shadows:** soft, diffused.

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
