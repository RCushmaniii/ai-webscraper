---
portfolio_enabled: true
portfolio_priority: 1
portfolio_featured: true
portfolio_last_reviewed: "2025-12-31"
title: "AI WebScraper  SEO Crawler & Analyzer"
tagline: "Enterprise-grade web crawling and SEO analysis platform"
slug: "ai-webscraper"
category: "Developer Tools"
target_audience: "Founders, Growth/SEO Teams, Platform & Data Engineers"
tags: ["web-crawler", "SEO", "FastAPI", "React", "Supabase", "Playwright"]
thumbnail: ""
hero_images: []
demo_video_url: ""
live_url: ""
case_study_url: ""
problem_solved: "Teams lack a reliable way to crawl modern (JS-heavy) sites, extract structured content and links, and perform actionable SEO analysis at scale."
key_outcomes:
  - "World-class dashboard with real-time crawl analytics"
  - "Automated stale-crawl detection and recovery"
  - "Secure multi-user access with RLS via Supabase"
tech_stack: ["React", "TypeScript", "Tailwind CSS", "FastAPI", "Supabase (PostgreSQL)", "Playwright", "BeautifulSoup4"]
complexity: "Production"
---

## Overview

AI WebScraper is a fullstack web crawling and SEO analysis platform. It reliably crawls websites (including JavaScriptrendered pages), extracts structured content, analyzes SEO signals, and presents insights in a modern dashboard. The system includes background monitoring to prevent stuck crawls, secure authentication with Supabase, and thoughtful UX for daytoday operations.

## Key Features

- Intelligent crawling with depth control, rate limiting, and robots.txt compliance
- JavaScript rendering via Playwright for dynamic sites
- SEO metadata and content extraction (headings, links, images)
- Link analysis with enhanced metrics and broken link detection
- Real-time dashboard: stats cards, recent activity, quick actions, and alerts
- Stale crawl monitoring service with auto markasfailed and manual override
- Authentication, RBAC-friendly routes, and Supabase Row Level Security (RLS)
- Batch operations (bulk delete/re-run) and export-ready data

## Architecture

- Frontend: React + TypeScript + Tailwind CSS
- Backend: FastAPI with services for crawl orchestration and monitoring
- Database: Supabase (managed PostgreSQL) with RLS
- Rendering/Parsing: Playwright for JS rendering; BeautifulSoup4 for HTML parsing
- Background Tasks: Crawl monitoring via FastAPI lifespan events

## Recent Results & Improvements

- v1.0.0 production release with redesigned dashboard and monitoring (see CHANGELOG.md)
- Implemented automated stale-crawl detection with configurable timeouts
- Added image extraction pipeline and enhanced links schema for deeper analysis

## My Role & Contributions

- Designed system architecture and database schema (Supabase + RLS)
- Implemented crawler services, monitoring worker, and API endpoints
- Built React dashboard, crawl list/detail pages, and new crawl flow
- Auth integration, error handling, and deployment documentation

## Timeline

- 20242025: Iterative development to production readiness
- 2025-12-27: v1.0.0 release with dashboard and monitoring

## Links

- Repository: https://github.com/RCushmaniii/ai-webscraper
- API Docs (local dev): http://localhost:8000/docs
- Frontend (local dev): http://localhost:3000

## Screenshots

<!-- Add images to docs/images/ and reference them here -->
<!-- Example: ![Dashboard](docs/images/dashboard.png) -->

## Tech Stack

- React, TypeScript, Tailwind CSS
- FastAPI, Pydantic
- Supabase (PostgreSQL, Auth, RLS)
- Playwright, BeautifulSoup4

## Setup (Dev)

See README.md for full instructions. Quick start:

`ash
# Backend
cd backend
python -m venv venv
./venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm start
`

---

Maintained by Robert Cushman
