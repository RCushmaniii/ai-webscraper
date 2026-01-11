# Backend Development Guide - AI Web Scraper

> **Purpose**: Backend-specific conventions, patterns, and best practices for Python/FastAPI development on this project.

---

## Tech Stack

- **Framework**: FastAPI 0.100+
- **Python**: 3.11+
- **Database Client**: Supabase Python SDK
- **Task Queue**: Celery + Redis
- **Web Scraping**: BeautifulSoup4, Playwright
- **Validation**: Pydantic v2

---

## Architecture Overview

```
backend/app/
├── api/               # HTTP endpoints
│   └── routes/       # Route handlers by resource
├── core/             # Core utilities
│   ├── auth.py       # Authentication middleware
│   ├── config.py     # Environment configuration
│   └── domain_blacklist.py  # Blacklisted domains
├── db/               # Database clients
│   └── supabase.py   # Supabase client factory
├── models/           # Pydantic models
│   └── models.py     # All data models
├── services/         # Business logic
│   ├── crawler.py    # Core crawling engine
│   ├── worker.py     # Celery tasks
│   └── issue_detector.py  # Issue detection
├── main.py           # FastAPI app entry
└── worker.py         # Celery worker entry
```

---

## Critical Patterns

### 1. Database Field Name Verification

**ALWAYS verify actual database column names before writing code.**

**Pattern**:
```python
# Step 1: Query database to verify schema
from supabase import create_client
from app.core.config import settings

client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
result = client.table("crawls").select("completed_at, created_at, updated_at").limit(1).execute()
print(result.data)  # Shows actual field names

# Step 2: Use correct field names in code
update_data = {
    "status": "completed",
    "completed_at": datetime.now().isoformat(),  # ✅ Matches database
    "updated_at": datetime.now().isoformat()
}
```

**Common Mismatches**:
- ❌ `finished_at` vs ✅ `completed_at`
- ❌ `follow_external` vs ✅ `follow_external_links`
- ❌ `started_at` vs ✅ `created_at`

---

### 2. Batch Database Operations

**Problem**: Individual inserts are slow (100ms per insert = 10 seconds for 100 items).

**Solution**: Batch operations (1 call for 100 items = 200ms total).

**Bad**:
```python
for link_data in links:
    db.table("links").insert(link_data).execute()  # 100 DB calls!
```

**Good**:
```python
# Collect all data first
links_to_save = []
for link in soup.find_all('a', href=True):
    link_data = {
        "id": str(uuid4()),
        "crawl_id": str(self.crawl.id),
        "target_url": absolute_url,
        # ... more fields
    }
    links_to_save.append(link_data)

# Save all at once
if links_to_save:
    db.table("links").insert(links_to_save).execute()  # 1 DB call!
    logger.info(f"Batch saved {len(links_to_save)} links")
```

**Apply to**:
- Links: `_save_links_batch()`
- Images: `_save_images_batch()`
- Issues: Batch insert when detecting issues
- SEO Metadata: Batch insert when possible

---

### 3. Logging Configuration

**Pattern**: Reduce verbosity of noisy libraries.

**In `main.py` and `worker.py`**:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Reduce verbosity of noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
```

**Why**: httpx logs every HTTP request at INFO level, creating log spam.

---

### 4. External Link Safety

**Always check before following external links**:

```python
from app.core.domain_blacklist import is_domain_blacklisted, get_blacklist_reason

# Before adding external link to queue
if not is_internal:
    # Check 1: Blacklist
    if is_domain_blacklisted(absolute_url):
        reason = get_blacklist_reason(absolute_url)
        logger.debug(f"Skipping blacklisted domain: {parsed_url.netloc} (reason: {reason})")
        continue

    # Check 2: Max external domains limit
    if parsed_url.netloc not in self.external_domains_crawled:
        if len(self.external_domains_crawled) >= self.crawl.max_external_links:
            logger.debug(f"Max external domains reached ({self.crawl.max_external_links})")
            continue

    # Safe to follow
    self.external_domains_crawled.add(parsed_url.netloc)
    logger.info(f"Following external link: {parsed_url.netloc}")
```

**Key Fields** (in `crawls` table):
- `follow_external_links`: Boolean flag
- `max_external_links`: Integer limit (default: 5)
- `external_depth`: How deep to crawl external sites (default: 1)

---

### 5. Row Level Security (RLS) Clients

**Two client types**:

1. **Auth Client** (user-scoped):
```python
from app.core.auth import get_auth_client

auth_client = get_auth_client()  # Uses user's JWT token
result = auth_client.table("crawls").select("*").execute()  # RLS enforced
```

2. **Service Client** (admin bypass):
```python
from supabase import create_client
from app.core.config import settings

service_client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY  # Bypasses RLS
)
result = service_client.table("crawls").select("*").execute()  # All rows visible
```

**When to use each**:
- **Auth Client**: API endpoints that serve user data
- **Service Client**: Celery background tasks, system operations

---

### 6. Pydantic Model Patterns

**Base -> Create -> Update -> InDB -> Response** pattern:

```python
class CrawlBase(BaseModel):
    """Fields that are settable by users"""
    url: str
    max_depth: int = 2
    max_pages: int = 100
    # ... user-controllable fields

class CrawlCreate(CrawlBase):
    """Fields required to create a crawl"""
    pass  # Inherits from Base

class CrawlUpdate(BaseModel):
    """Fields that can be updated (all optional)"""
    url: Optional[str] = None
    max_depth: Optional[int] = None
    # ... optional update fields

class CrawlInDB(CrawlBase):
    """Complete database representation"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    status: str = "pending"
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2

class CrawlResponse(CrawlBase):
    """API response (may hide sensitive fields)"""
    id: UUID
    status: str
    created_at: datetime
    # ... fields to return to client
```

**CRITICAL**: Field names must match database exactly!

---

### 7. Error Handling Patterns

**Check for foreign key violations** (crawl was deleted):

```python
try:
    result = db.table("links").insert(link_data).execute()

    if hasattr(result, "error") and result.error:
        error_msg = str(result.error)
        # Check for foreign key violation
        if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
            logger.warning(f"Crawl {crawl_id} was deleted. Stopping.")
            self.crawl_deleted = True
            return
        logger.error(f"Error saving link: {result.error}")

except Exception as e:
    error_msg = str(e)
    if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
        logger.warning(f"Crawl {crawl_id} was deleted. Stopping.")
        self.crawl_deleted = True
        return
    logger.error(f"Unexpected error: {e}")
```

---

### 8. Celery Task Patterns

**Task structure**:

```python
@celery_app.task(name="crawl_site")
def crawl_site(crawl_id: str):
    """
    Celery task to crawl a site.

    Args:
        crawl_id: UUID string of crawl to execute

    Returns:
        dict with crawl_id, status, error (if failed)
    """
    try:
        # 1. Fetch crawl from database (service role)
        service_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

        # 2. Update status to "running"
        service_client.table("crawls").update({
            "status": "running",
            "updated_at": datetime.now().isoformat()
        }).eq("id", crawl_id).execute()

        # 3. Execute crawl logic
        crawler = WebCrawler(crawl, db_client=service_client)
        await crawler.crawl()

        # 4. Update status to "completed" with timestamp
        service_client.table("crawls").update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),  # ✅ Match DB field
            "updated_at": datetime.now().isoformat(),
            "pages_crawled": progress.pages_crawled
        }).eq("id", crawl_id).execute()

        return {"crawl_id": crawl_id, "status": "completed"}

    except Exception as e:
        # 5. Mark as failed on error
        logger.exception(f"Error during crawl {crawl_id}")
        service_client.table("crawls").update({
            "status": "failed",
            "error": str(e)[:500],
            "completed_at": datetime.now().isoformat(),  # ✅ Still set timestamp
            "updated_at": datetime.now().isoformat()
        }).eq("id", crawl_id).execute()

        return {"crawl_id": crawl_id, "status": "failed", "error": str(e)}
```

---

## File-Specific Patterns

### `services/crawler.py`

**Key responsibilities**:
- BFS crawling with depth tracking
- Link extraction and classification (internal/external)
- External link safety (blacklist, limits)
- Batch database operations
- Graceful error handling

**Key methods**:
- `crawl()` - Main entry point
- `_process_url()` - Fetch and parse single URL
- `_extract_and_process_links()` - Extract links from HTML
- `_save_links_batch()` - Batch save links
- `_save_images_batch()` - Batch save images
- `get_progress()` - Return crawl progress metrics

**Critical tracking variables**:
```python
self.visited_urls: Set[str] = set()  # URLs already crawled
self.url_queue: List[Tuple[str, int, str]] = []  # (url, depth, referrer)
self.external_domains_crawled: Set[str] = set()  # External domains followed
self.crawl_deleted: bool = False  # Flag if crawl was deleted mid-execution
```

---

### `services/worker.py`

**Celery configuration**:
```python
celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,  # One task at a time
)
```

**Task definition**:
```python
@celery_app.task(name="crawl_site")
def crawl_site(crawl_id: str):
    """Main crawl task"""
    # ... implementation
```

---

### `api/routes/crawls.py`

**Pattern**: Routes use auth client for RLS enforcement.

```python
@router.post("/", response_model=CrawlResponse)
async def create_crawl(
    crawl: CrawlCreate,
    current_user: User = Depends(get_current_user)  # Auth required
):
    """Create a new crawl job."""
    auth_client = get_auth_client()  # Uses user's JWT

    # Insert with user_id for RLS
    crawl_data = {
        "id": str(uuid4()),
        "user_id": str(current_user.id),  # RLS policy enforces this
        "url": crawl.url,
        # ... more fields
    }

    response = auth_client.table("crawls").insert(crawl_data).execute()

    # Dispatch to Celery
    crawl_site.delay(str(crawl_id))

    return CrawlResponse(**response.data[0])
```

---

### `core/domain_blacklist.py`

**Purpose**: Prevent crawling problematic domains.

**Categories**:
- Social Media (18 domains): Facebook, Twitter, LinkedIn, etc.
- Analytics/Tracking (13 domains): Google Analytics, Segment, etc.
- Ad Networks (13 domains): Google Ads, Taboola, etc.
- CDNs (8 domains): Cloudflare, CloudFront, etc.
- Auth/Login (6 domains): Google accounts, Microsoft login, etc.
- Search Engines (7 domains): Google, Bing, DuckDuckGo, etc.
- E-commerce (7 domains): Amazon, eBay, Walmart, etc.
- File Sharing (7 domains): Google Drive, Dropbox, etc.

**Key functions**:
```python
def is_domain_blacklisted(url: str) -> bool:
    """Check if URL's domain is blacklisted."""
    # Returns True for blacklisted domains

def get_blacklist_reason(url: str) -> str:
    """Get category of blacklisted domain."""
    # Returns: "social_media", "analytics", "ads", etc.
```

---

## Environment Configuration

**`.env` structure**:
```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Admin key (bypasses RLS)
SUPABASE_ANON_KEY=eyJhbGc...          # Public key (RLS enforced)

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Feature Flags (default: false)
ENABLE_BATCH_CRAWLS=false
ENABLE_SELECTOR_SCRAPING=false
ENABLE_SEO_AUDIT=false
ENABLE_LLM=false

# Storage
STORAGE_DIR=./storage
```

**Access via**:
```python
from app.core.config import settings

url = settings.SUPABASE_URL
key = settings.SUPABASE_SERVICE_ROLE_KEY
```

---

## Testing & Debugging

### Manual Testing

**Start Celery worker**:
```bash
cd backend
celery -A app.worker worker --loglevel=info --pool=solo
```

**Trigger crawl**:
```python
from app.services.worker import crawl_site

# Synchronous (for debugging)
result = crawl_site("crawl-uuid-here")

# Asynchronous (production)
task = crawl_site.delay("crawl-uuid-here")
```

### Common Issues

**Issue**: Celery task not executing
- **Check**: Is Redis running? (`redis-cli ping`)
- **Check**: Is Celery worker running? (see logs)
- **Check**: Task name matches? (`@celery_app.task(name="crawl_site")`)

**Issue**: Database field not found
- **Solution**: Query database to verify field names
- **Solution**: Clear Python bytecode cache
- **Solution**: Restart Celery worker

**Issue**: RLS blocking operations
- **Check**: Using correct client? (auth_client vs service_client)
- **Check**: User has admin privileges? (`is_admin = true`)
- **Check**: RLS policies allow operation?

---

## Performance Optimization

### Database
- ✅ Batch inserts (100 items in 1 call)
- ✅ Use indexes on frequently queried columns
- ✅ Limit SELECT fields (don't `SELECT *` unless needed)
- ✅ Use pagination for large result sets

### Crawling
- ✅ Batch operations (links, images, issues)
- ✅ Respect rate limits (avoid overwhelming target sites)
- ✅ Use BeautifulSoup for static content (faster)
- ✅ Use Playwright only when JS rendering needed
- ✅ Limit external domain following (default: 5 domains max)
- ✅ Check blacklist before following external links

### Logging
- ✅ Set httpx/httpcore to WARNING level
- ✅ Use DEBUG level for verbose details
- ✅ Use INFO for important progress updates
- ✅ Use WARNING for recoverable issues
- ✅ Use ERROR for failures

---

## Security Checklist

Before deploying code, verify:

- [ ] All database tables use RLS policies
- [ ] API endpoints use `get_current_user()` dependency
- [ ] Service role key only used in Celery workers
- [ ] User inputs validated with Pydantic models
- [ ] SQL injection prevented (use parameterized queries)
- [ ] Sensitive data in environment variables (not hardcoded)
- [ ] Error messages don't expose internal details
- [ ] Rate limiting implemented for API endpoints
- [ ] CORS configured correctly (not `allow_origins=["*"]`)

---

## Migration Workflow

**1. Create migration file**:
```sql
-- database/migrations/006_add_new_feature.sql
ALTER TABLE crawls
ADD COLUMN new_field VARCHAR(255);

COMMENT ON COLUMN crawls.new_field IS 'Description of field';
```

**2. Run migration**:
- Open Supabase SQL Editor
- Paste migration SQL
- Execute

**3. Update Pydantic models**:
```python
# backend/app/models/models.py
class CrawlBase(BaseModel):
    # ... existing fields
    new_field: Optional[str] = None  # Add new field
```

**4. Clear bytecode cache**:
```bash
powershell -Command "Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force"
```

**5. Restart backend**:
```bash
# Restart uvicorn and Celery worker
```

---

## Code Review Checklist

Before committing backend code:

- [ ] Database field names verified against actual schema
- [ ] Batch operations used instead of loops with individual inserts
- [ ] External link safety checks implemented
- [ ] RLS client (auth vs service) chosen correctly
- [ ] Error handling includes foreign key violation checks
- [ ] Logging configured at appropriate levels
- [ ] Pydantic models match database schema
- [ ] Type hints used throughout
- [ ] Docstrings added to public functions
- [ ] No sensitive data hardcoded (use environment variables)

---

**Last Updated**: January 10, 2026
**Maintained By**: Claude (Anthropic) + CushLabs Team