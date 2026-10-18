/** @type {import('tailwindcss').Config} */
const { fontFamily } = require("tailwindcss/defaultTheme");

// Brand tokens follow the CushLabs brand kit
// (operating-system/cushlabs/brand-kit.md, canonical color source
// cushlabs/src/styles/global.css). Aligned 2026-10-18 — before that this file
// carried a slate-blue + Tailwind orange-500 theme that predated the kit.
//
//   One accent:  #FF6A3D (the site's live accent). #FD4C00 "Blaze Orange" is the
//                incoming brand color used by the chevron mark; it is the 600
//                step here so hover states already read as the new brand.
//   Neutrals:    pure greys from the kit (no slate/blue tint) carry structure.
//   Type:        Manrope for display, Inter for everything that is read.
//
// `primary-*` is the NEUTRAL scale (header, surfaces, text), `secondary-*` is
// the ACCENT scale — the names are historical and every page uses them, so the
// values were swapped underneath rather than renaming 500 class references.
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./index.html"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1200px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",

        // Neutral scale — brand greys. 900 is the kit's "near-black" card
        // field, 950 pure black, 800/700/600 the three surface steps.
        primary: {
          DEFAULT: "#0A0A0A",
          foreground: "#FFFFFF",
          50: "#F7F7F7",
          100: "#EEEEEE",
          200: "#DDDDDD",
          300: "#AAAAAA",
          400: "#888888",
          500: "#666666",
          600: "#2A2A2A",
          700: "#1A1A1A",
          800: "#141414",
          900: "#0A0A0A",
          950: "#000000",
        },

        // Accent scale — the one orange. 700+ are the kit's AA-safe text
        // tints (#BA4D2D is `--accent-text` on cushlabs.ai); use those for
        // small orange type on white, 500/600 for fills, rings and borders.
        secondary: {
          DEFAULT: "#FF6A3D",
          foreground: "#FFFFFF",
          hover: "#FD4C00",
          50: "#FFF3EE",
          100: "#FFE4DA",
          200: "#FFC7B3",
          300: "#FFA585",
          400: "#FF8A5E",
          500: "#FF6A3D",
          600: "#FD4C00",
          700: "#BA4D2D",
          800: "#8F3A22",
          900: "#6B2B19",
          950: "#3D170D",
        },

        neutral: {
          charcoal: "#111111", // kit: type on light backgrounds
          steel: "#666666", // kit: Grey 400, sub-copy
          cloud: "#F7F7F7", // app background (neutral, not blue-tinted)
        },

        success: {
          DEFAULT: "#10B981",
          50: "#ECFDF5",
          100: "#D1FAE5",
          500: "#10B981",
          600: "#059669",
        },
        error: {
          DEFAULT: "#EF4444",
          50: "#FEF2F2",
          100: "#FEE2E2",
          500: "#EF4444",
          600: "#DC2626",
        },

        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "12px",
        md: "8px",
        sm: "4px",
      },
      spacing: {
        "plush-container": "4rem",
        "plush-card": "2.5rem",
        "nav-height": "5rem",
      },
      fontFamily: {
        // Body face. Self-hosted in public/fonts, declared in src/index.css.
        sans: ["Inter", ...fontFamily.sans],
        // Display face for headings, buttons, labels, big numbers.
        display: ["Manrope", "Inter", ...fontFamily.sans],
      },
      lineHeight: {
        comfortable: "1.6",
      },
      boxShadow: {
        soft: "0 2px 8px rgba(0, 0, 0, 0.08)",
        "soft-lg": "0 4px 16px rgba(0, 0, 0, 0.12)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
