---
title: Design System & UI Spec
description: Visual system and UI guidelines for AI WebScraper.
category: Design
order: 2
---

# AI WebScraper — Design System & UI Spec

A practical design + UI specification for **AI WebScraper** (internal site crawling and analysis). This document is meant to stay close to how the app is currently implemented (React + Tailwind) while still providing clear direction for future UI work.

---

## 1. Brand Identity

### Brand Name

**AI WebScraper**

### Brand Positioning

Internal site crawler + analysis workspace. The UI should feel:

- Clear
- Operational
- Trustworthy
- Fast to scan

### Brand Voice

- Direct and practical
- Technical without jargon
- Confident without being salesy
- Calm under failure (good status/error states)

---

## 2. Color Palette

### Primary Colors

| Name           | Hex       | RGB           | Usage                  |
| -------------- | --------- | ------------- | ---------------------- |
| Blue (Primary) | `#2563EB` | 37, 99, 235   | Primary actions, links |
| Blue (Dark)    | `#1D4ED8` | 29, 78, 216   | Hover/active states    |
| Near-white     | `#F8FAFC` | 248, 250, 252 | App background         |

### Secondary / UI Colors

| Name      | Hex       | Usage                    |
| --------- | --------- | ------------------------ |
| Slate 900 | `#0F172A` | Header/footer background |
| Gray 50   | `#F9FAFB` | Page background (legacy) |
| Gray 100  | `#F3F4F6` | Panels                   |
| Gray 200  | `#E5E7EB` | Borders                  |
| Gray 600  | `#4B5563` | Secondary text           |
| Gray 900  | `#111827` | Primary text             |

### Theme Tokens (Current Implementation)

Tailwind colors resolve to CSS variables defined in `src/styles/globals.css`:

- `--background`, `--foreground`
- `--primary`, `--primary-foreground`
- `--secondary`, `--muted`, `--border`, `--ring`

When adding new colors, prefer extending tokens in `tailwind.config.js` instead of hardcoding colors in components.

---

## 3. Typography

### Font Stack

| Role           | Font Family                     | Weights | Source |
| -------------- | ------------------------------- | ------- | ------ |
| UI / Headlines | Inter, system-ui, -apple-system | 600-700 | Local  |
| Body           | Inter, system-ui, -apple-system | 400-500 | Local  |

### Type Scale

Use Tailwind’s default scale (`text-sm`, `text-base`, `text-lg`, `text-xl`, etc.). Prefer consistent hierarchy:

- Page title: `text-3xl font-bold`
- Section title: `text-xl font-semibold`
- Body: `text-base`
- Helper text: `text-sm text-muted-foreground`

### Typography Settings

| Element        | Font  | Weight | Line Height |
| -------------- | ----- | ------ | ----------- |
| Page Titles    | Inter | 700    | 1.2         |
| Section Titles | Inter | 600    | 1.3         |
| Body Text      | Inter | 400    | 1.6         |

---

## 4. Layout System

### Container

| Property  | Value                                |
| --------- | ------------------------------------ |
| Max Width | 1400px at `2xl` (Tailwind container) |
| Padding   | `2rem` (Tailwind container padding)  |

### Spacing

Use Tailwind spacing (`space-y-4`, `gap-6`, `p-6`, etc.). Preferred spacing defaults:

- Cards/panels: `p-6`
- Section spacing: `mb-8`
- Layout gaps: `gap-6` / `gap-8`

### Grid System

**Features Grid (2×2):**

- Fixed 2-column layout: `grid-template-columns: repeat(2, 1fr)`
- Max width: 900px
- Gap: `--space-lg`
- Breakpoint: Single column below 600px

---

## 5. Current App Implementation Notes

### Frontend Stack

- React 18 with Create React App
- React Router v6
- TailwindCSS
- Supabase Auth (frontend session)

### Styling Patterns (Current)

There are two styling patterns in the codebase today:

1. Tailwind utility classes in components (newer components)
2. A small set of utility classes in `src/index.css`:
   - `.card`
   - `.btn-primary`
   - `.btn-secondary`
   - `.input`
   - `.label`

When improving UI consistency, prefer consolidating toward Tailwind utilities or small reusable components.

### Language (EN/ES)

Some screens use bilingual labels directly in the UI (EN/ES in the same component). There is currently no centralized i18n system in this repo.

If we add proper i18n later, it should be done with a small translation layer and a single language source of truth.

### Theme (Light/Dark)

Theme tokens are implemented via CSS variables in `src/styles/globals.css` and Tailwind resolves them via `tailwind.config.js`. Dark mode is `class`-based.

---

## 6. JavaScript / Interaction Notes

- This project is a React SPA.
- Client-side interactivity is handled within React components.
- Navigation and page-level state are handled via React Router.

### Notes

- Any animation/interaction patterns should be implemented as React components.
- Prefer small, composable UI pieces and keep business logic outside UI components.

---

## 7. Animation Specifications (Optional)

### Entry Animations

| Element          | Animation   | Duration | Delay  | Easing        |
| ---------------- | ----------- | -------- | ------ | ------------- |
| Brand            | fadeSlideUp | 800ms    | 200ms  | ease-out-expo |
| Headline         | fadeSlideUp | 800ms    | 400ms  | ease-out-expo |
| Subheadline      | fadeSlideUp | 800ms    | 600ms  | ease-out-expo |
| Countdown        | fadeSlideUp | 800ms    | 800ms  | ease-out-expo |
| Lang Switcher    | fadeSlideUp | 800ms    | 1000ms | ease-out-expo |
| Scroll Indicator | fadeSlideUp | 800ms    | 1200ms | ease-out-expo |

### Scroll Animations

| Element          | Trigger     | Animation                                    |
| ---------------- | ----------- | -------------------------------------------- |
| .fade-in         | 10% visible | Opacity 0→1, translateY 40px→0               |
| .fade-in-stagger | 10% visible | Same + staggered delays (0, 100, 200, 300ms) |

### Ambient Animations

| Effect          | Type            | Duration | Iteration |
| --------------- | --------------- | -------- | --------- |
| Hero Glow Pulse | scale + opacity | 8s       | infinite  |
| Brand Dot Pulse | box-shadow      | 2s       | infinite  |
| Colon Blink     | opacity         | 1s       | infinite  |
| Scroll Line     | translateY      | 2s       | infinite  |

### Easing Functions

| Name           | Value                           | Usage             |
| -------------- | ------------------------------- | ----------------- |
| ease-out-expo  | `cubic-bezier(0.16, 1, 0.3, 1)` | Entry animations  |
| ease-out-quart | `cubic-bezier(0.25, 1, 0.5, 1)` | Hover transitions |

---

## 8. Responsive Breakpoints

| Breakpoint   | Width   | Changes                                 |
| ------------ | ------- | --------------------------------------- |
| Mobile       | < 480px | Tighter countdown spacing               |
| Small Tablet | < 600px | Features grid → single column           |
| Tablet       | < 768px | Hide scroll indicator, adjust countdown |
| Desktop      | 768px+  | Full layout, all effects enabled        |

---

## 9. Accessibility Compliance

### WCAG 2.1 AA Checklist

| Criterion                | Status | Implementation                                |
| ------------------------ | ------ | --------------------------------------------- |
| 1.1.1 Non-text Content   | ✅     | Alt text on images, aria-hidden on decorative |
| 1.4.3 Contrast (Minimum) | ✅     | 7:1+ for body text on dark background         |
| 1.4.10 Reflow            | ✅     | Responsive down to 320px                      |
| 2.1.1 Keyboard           | ✅     | All interactive elements focusable            |
| 2.3.1 Three Flashes      | ✅     | No flashing content                           |
| 2.4.1 Bypass Blocks      | ✅     | Semantic sections                             |
| 2.5.5 Target Size        | ✅     | Buttons meet 44×44px minimum                  |
| 3.1.1 Language of Page   | ✅     | `<html lang>` attribute                       |

### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 10. Metadata (Non-SEO)

This is primarily an internal tool. Keep metadata accurate for usability:

- `frontend/public/index.html`: title + description should reflect AI WebScraper
- Use consistent page titles in-app (route headings)

---

## 11. Documentation Files

- `README.md` (repo root) — Setup and overview
- `frontend/docs/BRAND.md` — Brand strategy & copy
- `frontend/docs/DESIGN.md` — Design system (this file)
- `frontend/docs/SUPABASE_SETUP.md` — Supabase notes / troubleshooting
- `frontend/docs/SETUP_INSTRUCTIONS.md` — Local setup

---

## 12. Version History

| Version | Date    | Changes                                                               |
| ------- | ------- | --------------------------------------------------------------------- |
| 1.0.0   | 2025-12 | Adapted from previous project and updated to match AI WebScraper repo |

---

_Document maintained for AI WebScraper_
