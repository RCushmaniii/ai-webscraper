# CushLabs Site Analysis - API Documentation (v1)

## API Overview

This backend is a FastAPI REST API for an **internal, admin-only** site analysis tool. v1 focuses on **content-first crawling** and **high-signal issue detection**.

**Base URL (v1):** `http://localhost:8000/api/v1`

## Authentication

All v1 endpoints require a Supabase JWT:

```http
Authorization: Bearer <supabase_jwt_token>
Content-Type: application/json
```

## Health

- `GET http://localhost:8000/health`

## Feature Flags (Default Off)

These capabilities exist in the codebase but are disabled in v1 unless enabled via env vars:

- `ENABLE_BATCH_CRAWLS`
- `ENABLE_SELECTOR_SCRAPING`
- `ENABLE_SEO_AUDIT`
- `ENABLE_LLM`

## Crawls

### Create Crawl

`POST /crawls`

Request body (minimal):

```json
{
  "url": "https://example.com"
}
```

Common optional fields:

```json
{
  "url": "https://example.com",
  "name": "Example",
  "max_depth": 2,
  "max_pages": 100,
  "respect_robots_txt": true,
  "follow_external_links": false,
  "js_rendering": false,
  "rate_limit": 2,
  "user_agent": null
}
```

### List Crawls

`GET /crawls`

Query params:

- `skip`
- `limit`
- `status`

### Get Crawl

`GET /crawls/{crawl_id}`

### Delete Crawl

`DELETE /crawls/{crawl_id}`

## Crawl Data

### Pages

`GET /crawls/{crawl_id}/pages`

Query params:

- `skip`
- `limit`
- `status_code`

### Links

`GET /crawls/{crawl_id}/links`

Query params:

- `skip`
- `limit`
- `is_internal`
- `is_broken`

### Issues

`GET /crawls/{crawl_id}/issues`

Query params:

- `skip`
- `limit`
- `severity`
- `issue_type`

## Optional Assets

### HTML Snapshot

`GET /crawls/{crawl_id}/html/{page_id}`

Returns:

```json
{
  "page_id": "...",
  "url": "https://example.com/page",
  "html_content": "<html>..."
}
```

### Screenshot

`GET /crawls/{crawl_id}/screenshot/{page_id}`

## Gated Endpoints (Return 404 Unless Enabled)

- `GET /crawls/{crawl_id}/audit` requires `ENABLE_SEO_AUDIT=true`
- `GET /crawls/{crawl_id}/summary` requires `ENABLE_LLM=true`

## Users

### Current User

`GET /users/me`
