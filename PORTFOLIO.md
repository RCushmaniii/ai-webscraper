---
# =============================================================================
# PORTFOLIO.MD — AI WebScraper
# =============================================================================
portfolio_enabled: true
portfolio_priority: 18
portfolio_featured: false
portfolio_last_reviewed: "2026-06-29"

title: "AI-Powered Web Scraper & SEO Analyzer"
tagline: "Crawl websites, detect SEO issues, and generate AI-powered analysis reports"
slug: "ai-webscraper"

category: "AI Automation"
target_audience: "Marketing teams and site owners who need actionable website insights"
tags:
  - "web-scraping"
  - "seo-analysis"
  - "ai-reports"
  - "data-extraction"
  - "crawling"
  - "fastapi"
  - "react"
  - "supabase"

thumbnail: "/images/portfolio/ai-webscraper-cover.webp"
slides:
  - src: "/images/portfolio/ai-webscraper-01.webp"
    alt_en: "Slide: 'Crawl smarter. Rank higher. Convert more.' — AI WebScraper shown beside an executive AI site-audit report"
    alt_es: "Diapositiva: 'Rastrea mejor. Posiciónate más alto. Convierte más.' — AI WebScraper junto a un reporte ejecutivo de auditoría del sitio con IA"
  - src: "/images/portfolio/ai-webscraper-02.webp"
    alt_en: "Slide: 'Data is not a strategy' — most SEO tools bury you in metrics; AI WebScraper answers what to fix first"
    alt_es: "Diapositiva: 'Los datos no son una estrategia' — la mayoría de las herramientas de SEO te abruman con métricas; AI WebScraper te dice qué corregir primero"
  - src: "/images/portfolio/ai-webscraper-03.webp"
    alt_en: "Slide: 'The intelligent consultant for your site' — raw crawl data flows through AI analysis into a prioritized action plan"
    alt_es: "Diapositiva: 'El consultor inteligente para tu sitio' — los datos del rastreo pasan por el análisis con IA y se convierten en un plan de acción priorizado"
  - src: "/images/portfolio/ai-webscraper-04.webp"
    alt_en: "Slide: 'From URL to action in 5 steps' — enter a URL, crawl the site, detect issues, analyze with AI, get copy-paste fixes"
    alt_es: "Diapositiva: 'De la URL a la acción en 5 pasos' — ingresa una URL, rastrea el sitio, detecta problemas, analiza con IA y obtén correcciones listas para copiar y pegar"
  - src: "/images/portfolio/ai-webscraper-05.webp"
    alt_en: "Slide: 'Surfacing the signals that matter' — detected issues grouped by severity into critical, high, and medium priority"
    alt_es: "Diapositiva: 'Resaltamos las señales que importan' — los problemas detectados se agrupan por gravedad en prioridad crítica, alta y media"
  - src: "/images/portfolio/ai-webscraper-06.webp"
    alt_en: "Slide: 'More than a crawler, a strategic engine' — impact-versus-effort prioritization with before-and-after copy-paste fixes"
    alt_es: "Diapositiva: 'Más que un rastreador, un motor estratégico' — priorización por impacto contra esfuerzo con correcciones de antes y después listas para copiar y pegar"
  - src: "/images/portfolio/ai-webscraper-07.webp"
    alt_en: "Slide: 'Built for the entire growth team' — business owners, marketing managers, agencies, and content/web teams"
    alt_es: "Diapositiva: 'Hecho para todo el equipo de crecimiento' — dueños de negocios, gerentes de marketing, agencias y equipos de contenido y web"
  - src: "/images/portfolio/ai-webscraper-08.webp"
    alt_en: "Slide: 'From website crawl to growth roadmap' — enter your website URL and start a free AI audit"
    alt_es: "Diapositiva: 'Del rastreo del sitio web a una hoja de ruta de crecimiento' — ingresa la URL de tu sitio e inicia una auditoría con IA gratis"
hero_images: []
demo_video_url: "/video/ai-webscraper-brief.mp4"
demo_video_poster: "/images/portfolio/ai-webscraper-brief-poster.webp"

live_url: "https://scraper.cushlabs.ai"
demo_url: ""
case_study_url: ""

problem_solved: |
  Organizations need to understand their website health — broken links, missing SEO metadata,
  thin content, accessibility gaps — but enterprise tools cost thousands per year and manual
  audits don't scale. This platform automates the entire crawl-analyze-report pipeline with
  AI-generated insights at a fraction of the cost.

key_outcomes:
  - "1,150+ pages crawled and analyzed per session with sub-2s per-page processing"
  - "11 SEO issue categories detected automatically across every crawl"
  - "GPT-4 powered reports with executive summaries and actionable recommendations"
  - "Tier-based access system ready for SaaS monetization"

tech_stack:
  - "React 18"
  - "Vite"
  - "TypeScript"
  - "FastAPI"
  - "Python 3.11"
  - "Supabase (PostgreSQL)"
  - "OpenAI GPT-4"
  - "Playwright"
  - "BeautifulSoup4"
  - "TailwindCSS"
  - "Docker"

complexity: "Production"

# === REPO HEALTH STATUS ===
# Last audited: 2026-06-29
# Standards defined in: operating-system/delivery/repo-health-baseline.md
health_status:
  sentry: "Y"
  testing: "Y"
  ci_cd: "Y"
  health_endpoint: "Y"
  security_headers: "Y"
  rate_limiting: "Y"
  env_validation: "-"
  analytics: "Y"
  structured_logging: "-"
  dependabot: "Y"
  secret_scanning: "Y"
  db_backup: "-"
---

## Overview

AI WebScraper is a full-stack web crawling and site analysis platform that combines intelligent crawling with automated SEO auditing and AI-powered reporting. It crawls websites starting from a URL, extracts SEO metadata and content metrics, detects technical issues across 11 categories, and generates comprehensive reports using GPT-4.

The platform is built with a React/TypeScript (Vite) frontend, FastAPI backend, in-process async task processing (asyncio — no external queue), and Supabase for authentication and data storage with Row Level Security on all tables. It includes a tiered access system (free: 3 crawls, admin: unlimited) designed for eventual SaaS monetization.

## The Challenge

Website owners and marketing teams face a common problem: understanding what's actually wrong with their site.

- **Enterprise SEO tools are expensive.** Ahrefs, SEMrush, and Screaming Frog charge hundreds to thousands per year. Small businesses and freelancers can't justify the cost for occasional audits.
- **Manual audits don't scale.** Checking every page for missing titles, broken links, thin content, and accessibility issues is tedious and error-prone beyond a few dozen pages.
- **Raw crawl data isn't actionable.** Even when you can crawl a site, translating the data into prioritized recommendations requires SEO expertise most teams don't have.

## The Solution

**Intelligent crawling with safety controls:**
The crawler uses navigation detection to prioritize important pages, enforces depth and page limits, respects robots.txt, and maintains a 200+ domain blacklist to prevent runaway crawls into social media and ad networks.

**Automated SEO issue detection:**
Every crawl runs 11 detection checks — broken internal links, broken images, missing H1 tags, thin content (<300 words), duplicate titles and descriptions, missing alt text, orphan pages, and oversized pages. Issues are categorized by severity (critical/high/medium/low).

**AI-powered analysis reports:**
GPT-4 generates executive summaries with site health scores, performance metrics, content analysis, and prioritized recommendations. Reports include status code distribution, response time analysis, link structure, and image accessibility coverage — all structured via Pydantic for consistent output.

**Tier-based access:**
Free users get 3 crawls to evaluate the platform. Admin users get unlimited access with user management capabilities. The usage endpoint and frontend show remaining crawls transparently.

## Technical Highlights

- **Batch database operations:** Links, images, and pages saved in single INSERT calls instead of per-record, achieving sub-2s per-page processing
- **Navigation scoring:** Custom NavDetector analyzes HTML structure, CSS classes, and URL patterns to identify and prioritize primary navigation pages
- **Domain blacklist:** 200+ domains across 9 categories (social media, analytics, ad networks, CDNs, auth systems) prevent infinite crawl loops
- **Structured AI outputs:** OpenAI Instructor library enforces Pydantic schemas on GPT-4 responses for consistent, typed report data
- **Row Level Security:** Every database table uses RLS policies — users only see their own data, service role handles background processing
- **Stale crawl detection:** Auto-detects crawls stuck longer than 30 minutes and allows manual failure marking

## Results

**For the End User:**

- Complete site audit in minutes instead of hours of manual checking
- Actionable AI-generated recommendations prioritized by severity
- Accessible to non-technical users through a clean web interface
- Free tier available for evaluation without commitment

**Technical Demonstration:**

- Full-stack production architecture: React (Vite) + FastAPI + Supabase, async in-process task processing, Dockerized on a Hetzner VPS behind Caddy
- Async crawling with rate limiting, depth control, and safety boundaries
- LLM integration with structured outputs, token tracking, and cost budgeting
- Security-first design with RLS, JWT auth, and tiered access control

The project demonstrates end-to-end platform engineering — from async task orchestration to AI integration to user-facing SaaS patterns.
