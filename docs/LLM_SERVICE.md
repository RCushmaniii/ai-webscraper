# LLM Service Layer Documentation

## Overview

The LLM Service Layer provides AI-powered content analysis for the AI WebScraper platform. It uses OpenAI's API with structured outputs (via Instructor) to analyze crawled pages and generate actionable insights.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Routes                                │
│              /api/v1/analysis/*                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Content Analyzer                              │
│              High-level orchestration                            │
│        • analyze_page_basic()                                   │
│        • analyze_page_detailed()                                │
│        • generate_crawl_report()                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Service                                 │
│              Core abstraction layer                              │
│        • Structured outputs with Pydantic                       │
│        • Cost tracking                                          │
│        • Retry logic                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenAI + Instructor                           │
│              API calls with validation                           │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```powershell
cd backend
pip install openai instructor tiktoken
# Or add to requirements.txt and:
pip install -r requirements.txt
```

### 2. Configure Environment

Add to your `backend/.env`:

```env
OPENAI_API_KEY=sk-your-key-here
ENABLE_LLM_BASIC=true
ENABLE_LLM_ANALYSIS=true
ENABLE_LLM_REPORTS=true
MAX_LLM_COST_PER_CRAWL=5.0
```

### 3. Register API Routes

Add to `backend/app/api/api.py`:

```python
from app.api.routes import analysis

api_router.include_router(analysis.router, tags=["analysis"])
```

### 4. Run Database Migration

Run `database/migrations/003_llm_analysis_tables.sql` in Supabase SQL editor.

## Usage Examples

### Basic Page Analysis

```python
from app.services.content_analyzer import ContentAnalyzer

# Create analyzer
analyzer = ContentAnalyzer(crawl_id="abc123")

# Analyze a page (Tier 1 - fast and cheap)
result = await analyzer.analyze_page_basic(
    url="https://example.com/about",
    content="We are a company that...",
    title="About Us"
)

# Result includes:
# - summary: Page summary with purpose and audience
# - category: Page type (blog, product, landing, etc.)
# - topics: Keywords and topics extracted
```

### Detailed Analysis

```python
# More comprehensive analysis (Tier 1 + Tier 2)
result = await analyzer.analyze_page_detailed(
    url="https://example.com/product",
    content="Our flagship product...",
    title="Product Name",
    meta_description="Buy our product...",
    h1="Product Name - Best in Class",
    word_count=1500
)

# Adds:
# - content_quality: Quality score and feedback
# - seo_analysis: SEO recommendations
# - meta_suggestion: Generated meta description
```

### Generate Crawl Report

```python
# Generate executive summary (Tier 3)
report = await analyzer.generate_crawl_report(
    crawl_data={
        "base_url": "https://example.com",
        "total_pages": 50,
        "broken_links": 3,
        # ... other metrics
    },
    page_analyses=[
        # Previously analyzed pages
    ]
)

# Report includes:
# - executive_summary: Overall site health assessment
# - content_strategy: Content recommendations
# - brand_voice: Voice consistency analysis
```

### Direct LLM Service Usage

```python
from app.services.llm_service import LLMService

service = LLMService(crawl_id="abc123")

# Get page summary
summary = await service.analyze_page_summary(
    content="Page content here...",
    url="https://example.com/page",
    title="Page Title"
)

print(summary.summary)  # "This page describes..."
print(summary.page_purpose)  # "inform"
print(summary.target_audience)  # "developers"

# Check usage
usage = service.get_usage_summary()
print(f"Total cost: ${usage['total_cost_usd']:.4f}")
```

### Get Embeddings for Semantic Search

```python
# Get embedding for semantic similarity
embedding = await service.get_embedding("Page content here...")

# Returns: List[float] with 512 dimensions
```

## API Endpoints

### Status & Configuration

```
GET /api/v1/analysis/status
```

Returns LLM service status and which features are enabled.

```
GET /api/v1/analysis/tasks
```

Lists all available analysis tasks with configurations.

### Page Analysis

```
POST /api/v1/analysis/page
```

Analyze a single page with content.

Request:

```json
{
  "url": "https://example.com/page",
  "content": "Page content...",
  "title": "Page Title",
  "analysis_level": "basic" // "basic", "detailed", or "full"
}
```

```
POST /api/v1/analysis/url
```

Fetch and analyze a URL directly.

### Specific Analyses

```
POST /api/v1/analysis/content-quality
POST /api/v1/analysis/seo-recommendations
POST /api/v1/analysis/meta-description
POST /api/v1/analysis/categorize
POST /api/v1/analysis/extract-topics
POST /api/v1/analysis/images/alt-text
```

## Task Tiers & Cost Estimation

### Tier 1: Basic (Run During Crawl)

| Task             | Model       | Est. Cost/Page |
| ---------------- | ----------- | -------------- |
| Page Summary     | gpt-4o-mini | $0.0005        |
| Categorization   | gpt-4o-mini | $0.0003        |
| Topic Extraction | gpt-4o-mini | $0.0003        |
| Title Quality    | gpt-4o-mini | $0.0002        |

**Total Tier 1:** ~$0.0013/page

### Tier 2: Detailed (On-Demand)

| Task                 | Model       | Est. Cost/Page |
| -------------------- | ----------- | -------------- |
| Content Quality      | gpt-4o-mini | $0.002         |
| SEO Recommendations  | gpt-4o-mini | $0.002         |
| Alt Text Suggestions | gpt-4o-mini | $0.001         |
| Meta Description     | gpt-4o-mini | $0.001         |

**Total Tier 2:** ~$0.006/page

### Tier 3: Synthesis (Per Crawl)

| Task              | Model  | Est. Cost/Crawl |
| ----------------- | ------ | --------------- |
| Executive Summary | gpt-4o | $0.10-0.20      |
| Brand Voice       | gpt-4o | $0.10-0.20      |
| Content Strategy  | gpt-4o | $0.10-0.20      |

**Total Tier 3:** ~$0.30-0.60/crawl

### Cost Examples

| Site Size | Tier 1 Only | + Tier 2 | + Tier 3 |
| --------- | ----------- | -------- | -------- |
| 10 pages  | $0.013      | $0.073   | $0.40    |
| 50 pages  | $0.065      | $0.365   | $0.70    |
| 100 pages | $0.13       | $0.73    | $1.00    |
| 500 pages | $0.65       | $3.65    | $4.00    |

## Feature Flags

Control which tiers are enabled:

```env
# Tier 1: Basic analysis
ENABLE_LLM_BASIC=true

# Tier 2: Detailed analysis
ENABLE_LLM_ANALYSIS=true

# Tier 3: Synthesis reports
ENABLE_LLM_REPORTS=true

# Embeddings
ENABLE_EMBEDDINGS=true
```

## Structured Output Models

All LLM responses are validated Pydantic models:

```python
class PageSummary(BaseModel):
    summary: str
    page_purpose: str
    target_audience: Optional[str]
    key_message: Optional[str]
    content_type: str

class ContentQualityAnalysis(BaseModel):
    overall_score: int  # 0-100
    clarity_score: int
    relevance_score: int
    engagement_score: int
    structure_score: int
    strengths: List[ContentStrength]
    weaknesses: List[ContentWeakness]
    quick_wins: List[str]
    summary: str

class SEOAnalysis(BaseModel):
    seo_score: int  # 0-100
    recommendations: List[SEORecommendation]
    target_keywords: List[str]
    keyword_opportunities: List[str]
```

See `backend/app/models/llm_models.py` for all models.

## Cost Tracking

Every LLM call is tracked:

```python
# After analysis
usage = service.get_usage_summary()
# {
#     "crawl_id": "abc123",
#     "total_cost_usd": 0.0043,
#     "total_input_tokens": 12500,
#     "total_output_tokens": 1200,
#     "request_count": 15,
#     "budget_remaining_usd": 4.9957
# }

# Get detailed records
records = service.get_usage_records()
# List of LLMUsageRecord objects
```

Budget enforcement:

```python
# Service will raise BudgetExceededError if cost exceeds MAX_LLM_COST_PER_CRAWL
try:
    result = await service.analyze_content_quality(...)
except BudgetExceededError:
    # Handle gracefully - skip remaining analysis
    pass
```

## Error Handling

```python
from app.services.llm_service import (
    LLMServiceError,
    TaskDisabledError,
    BudgetExceededError,
    RateLimitError
)

try:
    result = await service.analyze_page_summary(content, url)
except TaskDisabledError:
    # Feature flag disabled
    pass
except BudgetExceededError:
    # Cost limit hit
    pass
except RateLimitError:
    # OpenAI rate limit
    await asyncio.sleep(60)
    # Retry
except LLMServiceError as e:
    # Other LLM errors
    logger.error(f"LLM error: {e}")
```

## Integration with Crawler

To add LLM analysis during crawl:

```python
# In your crawler service
from app.services.content_analyzer import ContentAnalyzer

async def process_page(self, page_data: dict):
    # ... existing crawl logic ...

    # Add LLM analysis if enabled
    if settings.ENABLE_LLM_BASIC:
        analyzer = ContentAnalyzer(crawl_id=self.crawl_id)

        analysis = await analyzer.analyze_page_basic(
            url=page_data["url"],
            content=page_data["content"],
            title=page_data["title"]
        )

        # Store analysis results
        await self.save_page_analysis(page_data["id"], analysis)
```

## Database Schema

Key tables:

- `page_analysis` - Per-page analysis results
- `crawl_analysis` - Per-crawl synthesis reports
- `page_embeddings` - Vector embeddings for semantic search
- `llm_usage` - Cost and usage tracking
- `image_analysis` - Image audit with alt text suggestions

See `database/migrations/003_llm_analysis_tables.sql` for full schema.

## Best Practices

1. **Start with Tier 1** - Run basic analysis during crawl, it's cheap
2. **Tier 2 on demand** - Let users request detailed analysis
3. **Tier 3 after completion** - Generate reports only after crawl finishes
4. **Monitor costs** - Check usage summaries regularly
5. **Handle errors gracefully** - Don't let LLM failures break crawls
6. **Cache embeddings** - Only regenerate if content changes (use content_hash)

## Troubleshooting

### "OpenAI API key not configured"

- Check `OPENAI_API_KEY` in `.env`
- Ensure the key is valid and has credits

### "Task disabled by feature flags"

- Check `ENABLE_LLM_*` flags in `.env`
- Ensure the specific tier is enabled

### "Budget exceeded"

- Increase `MAX_LLM_COST_PER_CRAWL` if needed
- Or run fewer analyses per crawl

### High latency

- GPT-4o is slower than GPT-4o-mini
- Consider reducing Tier 3 analyses
- Use concurrency limits for batch operations

### Token limit errors

- Content is truncated automatically
- For very long pages, summary may be less accurate
