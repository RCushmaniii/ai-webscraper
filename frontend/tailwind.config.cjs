/** @type {import('tailwindcss').Config} */
const { fontFamily } = require('tailwindcss/defaultTheme')

module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1200px", // Max width per brand guidelines
      },
    },
    extend: {
      colors: {
        // Brand colors from BRAND.md - "Plush" Deep Slate & Orange theme
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",

        // Primary: Deep Slate (for header/nav)
        primary: {
          DEFAULT: "#1E293B", // slate-800
          foreground: "#FFFFFF",
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B", // Brand primary
          900: "#0F172A",
          950: "#020617",
        },

        // Secondary: Warm Orange (for buttons/actions)
        secondary: {
          DEFAULT: "#F97316", // orange-500
          foreground: "#FFFFFF",
          hover: "#EA580C", // orange-600
          50: "#FFF7ED",
          100: "#FFEDD5",
          200: "#FED7AA",
          300: "#FDBA74",
          400: "#FB923C",
          500: "#F97316", // Brand action color
          600: "#EA580C", // Brand action hover
          700: "#C2410C",
          800: "#9A3412",
          900: "#7C2D12",
          950: "#431407",
        },

        // Neutral grays for text
        neutral: {
          charcoal: "#1F2937", // gray-800 - primary text
          steel: "#64748B", // slate-500 - secondary text
          cloud: "#F8FAFC", // slate-50 - app background
        },

        // Status colors
        success: {
          DEFAULT: "#10B981", // emerald-500
          50: "#ECFDF5",
          100: "#D1FAE5",
          500: "#10B981",
          600: "#059669",
        },
        error: {
          DEFAULT: "#EF4444", // red-500
          50: "#FEF2F2",
          100: "#FEE2E2",
          500: "#EF4444",
          600: "#DC2626",
        },

        // Aliases
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
        lg: "12px", // Brand guideline: 12px soft corners
        md: "8px",
        sm: "4px",
      },
      spacing: {
        // Plush padding values from brand guidelines
        'plush-container': '4rem', // 64px for containers
        'plush-card': '2.5rem', // 40px for cards
        'nav-height': '5rem', // 80px for nav bar
      },
      fontFamily: {
        sans: ["Inter", "Roboto", "Open Sans", ...fontFamily.sans],
      },
      lineHeight: {
        'comfortable': '1.6', // Brand guideline for body text
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.08)', // Soft, diffused shadows
        'soft-lg': '0 4px 16px rgba(0, 0, 0, 0.12)',
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
      }
    },
  },
  plugins: [require("tailwindcss-animate")],
}