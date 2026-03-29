"""
Analysis API Routes

Endpoints for triggering LLM-powered content analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
import io

from app.services.llm_service import LLMService, TaskDisabledError, BudgetExceededError
from app.services.content_analyzer import ContentAnalyzer, quick_analyze_url
from app.services.semantic_builder import build_semantic_skeleton, build_voice_fingerprint
from app.core.llm_config import get_llm_settings, LLMTask, get_task_config, is_task_enabled
from app.core.auth import get_current_user, get_auth_client
from app.models.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


# =========================================
# Request/Response Models
# =========================================

class AnalyzePageRequest(BaseModel):
    """Request to analyze a single page"""
    url: str = Field(..., description="URL of the page")
    content: str = Field(..., description="Text content of the page")
    title: Optional[str] = Field(None, description="Page title")
    meta_description: Optional[str] = Field(None, description="Meta description")
    h1: Optional[str] = Field(None, description="H1 heading")
    word_count: Optional[int] = Field(0, description="Word count")
    analysis_level: str = Field(
        "basic",
        description="Analysis level: 'basic', 'detailed', or 'full'"
    )


class AnalyzeUrlRequest(BaseModel):
    """Request to fetch and analyze a URL"""
    url: HttpUrl = Field(..., description="URL to analyze")
    analysis_level: str = Field("basic", description="Analysis level")


class AnalyzeCrawlRequest(BaseModel):
    """Request to analyze all pages in a crawl"""
    crawl_id: str = Field(..., description="Crawl ID to analyze")
    analysis_level: str = Field("basic", description="Analysis level for pages")
    generate_report: bool = Field(True, description="Generate executive report")


class GenerateReportRequest(BaseModel):
    """Request to generate report for a crawl"""
    crawl_id: str = Field(..., description="Crawl ID")


class AltTextRequest(BaseModel):
    """Request to suggest alt text for images"""
    images: List[Dict[str, Any]] = Field(..., description="List of images")
    page_content: str = Field(..., description="Page content for context")


class LLMStatusResponse(BaseModel):
    """LLM service status response"""
    enabled: bool
    provider: str
    tasks_enabled: Dict[str, bool]
    cost_settings: Dict[str, float]


class UsageSummaryResponse(BaseModel):
    """Usage summary response"""
    crawl_id: str
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    request_count: int
    budget_remaining_usd: float


# =========================================
# Status Endpoints
# =========================================

@router.get("/status", response_model=LLMStatusResponse)
async def get_llm_status():
    """
    Get LLM service status and configuration.
    
    Returns which features are enabled and cost settings.
    """
    settings = get_llm_settings()
    
    tasks_enabled = {}
    for task in LLMTask:
        tasks_enabled[task.value] = is_task_enabled(task, settings)
    
    return LLMStatusResponse(
        enabled=bool(settings.openai_api_key),
        provider=settings.default_provider.value,
        tasks_enabled=tasks_enabled,
        cost_settings={
            "max_cost_per_crawl": settings.max_cost_per_crawl,
            "warn_threshold": settings.warn_cost_threshold,
        }
    )


@router.get("/tasks")
async def list_available_tasks():
    """
    List all available LLM tasks with their configurations.
    """
    settings = get_llm_settings()
    
    tasks = []
    for task in LLMTask:
        config = get_task_config(task)
        tasks.append({
            "task": task.value,
            "description": config.description,
            "tier": config.tier,
            "model": config.model,
            "enabled": is_task_enabled(task, settings),
            "estimated_cost_per_call": f"${config.cost_per_1k_input * 2 + config.cost_per_1k_output * 0.5:.6f}"
        })
    
    return {"tasks": tasks}


# =========================================
# Single Page Analysis
# =========================================

@router.post("/page")
async def analyze_page(request: AnalyzePageRequest):
    """
    Analyze a single page with LLM.
    
    Supports three analysis levels:
    - basic: Summary, categorization, topics (Tier 1)
    - detailed: + Content quality, SEO recommendations (Tier 2)
    - full: + Title assessment, all available analyses
    """
    try:
        analyzer = ContentAnalyzer(crawl_id="api_request")
        
        if request.analysis_level == "basic":
            result = await analyzer.analyze_page_basic(
                url=request.url,
                content=request.content,
                title=request.title,
                meta_description=request.meta_description,
            )
        elif request.analysis_level == "detailed":
            result = await analyzer.analyze_page_detailed(
                url=request.url,
                content=request.content,
                title=request.title,
                meta_description=request.meta_description,
                h1=request.h1,
                word_count=request.word_count or 0,
            )
        else:  # full
            result = await analyzer.analyze_page_full(
                url=request.url,
                content=request.content,
                title=request.title,
                meta_description=request.meta_description,
                h1=request.h1,
                word_count=request.word_count or 0,
            )
        
        # Add usage info
        result["usage"] = analyzer.get_usage_summary()
        
        return result
        
    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=f"LLM feature disabled: {e}")
    except BudgetExceededError as e:
        raise HTTPException(status_code=402, detail=f"Budget exceeded: {e}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/url")
async def analyze_url(request: AnalyzeUrlRequest):
    """
    Fetch a URL and analyze its content.
    
    Convenience endpoint that handles fetching the page.
    """
    try:
        result = await quick_analyze_url(str(request.url))
        return result
        
    except Exception as e:
        logger.error(f"URL analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# Image Analysis
# =========================================

@router.post("/images/alt-text")
async def suggest_alt_text(request: AltTextRequest):
    """
    Generate alt text suggestions for images.
    
    Provide images with their context and get AI-generated alt text.
    """
    try:
        analyzer = ContentAnalyzer(crawl_id="api_request")
        
        results = await analyzer.analyze_images_batch(
            images=request.images,
            page_content=request.page_content
        )
        
        return {
            "suggestions": results,
            "usage": analyzer.get_usage_summary()
        }
        
    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=f"LLM feature disabled: {e}")
    except Exception as e:
        logger.error(f"Alt text generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# Crawl Analysis
# =========================================

@router.post("/crawl/{crawl_id}/analyze")
async def analyze_crawl(
    crawl_id: str,
    background_tasks: BackgroundTasks,
    analysis_level: str = "basic",
):
    """
    Trigger LLM analysis for all pages in a crawl.
    
    This runs in the background and updates the database.
    """
    # TODO: Implement database integration
    # For now, return a placeholder
    
    return {
        "status": "queued",
        "crawl_id": crawl_id,
        "analysis_level": analysis_level,
        "message": "Analysis has been queued. Check crawl status for progress."
    }


@router.post("/crawl/{crawl_id}/report")
async def generate_crawl_report(
    crawl_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive executive report for a completed crawl.

    This endpoint produces a world-class website analysis report including:
    - Executive summary with AI-powered insights
    - Technical SEO metrics and performance data
    - Content quality analysis
    - Issue breakdown by severity and category
    - Actionable recommendations with priority ranking
    - Page-level insights for top and problem pages
    """
    from statistics import mean, median
    from supabase import create_client
    from app.core.config import settings

    # Use service role client to bypass RLS for reading related tables
    # User is already authenticated via get_current_user
    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    try:
        # =============================================
        # PHASE 1: DATA COLLECTION
        # =============================================

        # 1. Fetch crawl data
        crawl_response = supabase_client.table("crawls").select("*").eq("id", crawl_id).single().execute()
        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        crawl = crawl_response.data

        # Security check: verify user owns this crawl
        if str(crawl.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to access this crawl")

        # Check if crawl is completed
        if crawl.get("status") not in ["completed", "stopped"]:
            raise HTTPException(
                status_code=400,
                detail=f"Crawl must be completed before generating report. Current status: {crawl.get('status')}"
            )

        # 2. Fetch comprehensive page data
        # Note: Using actual column names from database (content_length instead of word_count)
        pages_response = supabase_client.table("pages").select(
            "id, url, title, meta_description, status_code, content_length, "
            "response_time, content_type, seo_score, h1_tags, h2_tags, internal_links, "
            "external_links, images, nav_score, is_primary, depth"
        ).eq("crawl_id", crawl_id).execute()
        pages = pages_response.data or []

        # Map content_length to word_count for compatibility with rest of code
        for page in pages:
            page["word_count"] = page.get("content_length", 0)

        # 3. Fetch all issues with full details
        issues_response = supabase_client.table("issues").select("*").eq("crawl_id", crawl_id).execute()
        issues = issues_response.data or []

        # 4. Fetch links data for comprehensive link analysis
        # Note: Using actual column names (is_internal instead of link_type)
        links_response = supabase_client.table("links").select(
            "id, source_page_id, target_url, is_internal, is_broken, status_code, anchor_text, nav_score, is_navigation"
        ).eq("crawl_id", crawl_id).execute()
        links = links_response.data or []

        # Map is_internal to link_type for compatibility
        for link in links:
            link["link_type"] = "internal" if link.get("is_internal") else "external"

        # 5. Fetch SEO metadata (via page_ids)
        page_ids = [p.get("id") for p in pages if p.get("id")]
        seo_data = []
        if page_ids:
            seo_response = supabase_client.table("seo_metadata").select(
                "id, page_id, title, title_length, meta_description, meta_description_length, "
                "h1, h2, canonical, robots_meta, og_tags, image_alt_missing_count"
            ).in_("page_id", page_ids).execute()
            seo_data = seo_response.data or []

        # 6. Fetch images data
        # Note: Using actual column names (alt instead of alt_text, no file_size)
        images_response = supabase_client.table("images").select(
            "id, src, alt, has_alt, width, height"
        ).eq("crawl_id", crawl_id).execute()
        images = images_response.data or []

        # Map alt to alt_text for compatibility
        for img in images:
            img["alt_text"] = img.get("alt")

        # =============================================
        # PHASE 2: METRICS CALCULATION
        # =============================================

        total_pages = len(pages)

        # --- Status Code Analysis ---
        status_2xx = [p for p in pages if 200 <= (p.get("status_code") or 0) < 300]
        status_3xx = [p for p in pages if 300 <= (p.get("status_code") or 0) < 400]
        status_4xx = [p for p in pages if 400 <= (p.get("status_code") or 0) < 500]
        status_5xx = [p for p in pages if (p.get("status_code") or 0) >= 500]

        # --- Performance Metrics ---
        response_times = [p.get("response_time") for p in pages if p.get("response_time")]

        avg_response_time = round(mean(response_times), 2) if response_times else 0
        median_response_time = round(median(response_times), 2) if response_times else 0
        slowest_pages = sorted(
            [p for p in pages if p.get("response_time")],
            key=lambda x: x.get("response_time", 0),
            reverse=True
        )[:5]

        # Note: page_size_bytes not tracked in current schema
        avg_page_size = 0
        largest_pages = []

        # --- Content Metrics ---
        word_counts = [p.get("word_count") for p in pages if p.get("word_count")]
        avg_word_count = round(mean(word_counts)) if word_counts else 0
        thin_content_pages = [p for p in pages if p.get("word_count") and p.get("word_count") < 300]
        content_rich_pages = [p for p in pages if p.get("word_count") and p.get("word_count") >= 1000]

        # --- SEO Metrics ---
        seo_map = {s.get("page_id"): s for s in seo_data}
        missing_title = [p for p in pages if not p.get("title") or p.get("title") == "No title found"]
        missing_meta_desc = [s for s in seo_data if not s.get("meta_description")]
        missing_h1 = [s for s in seo_data if not s.get("h1")]
        duplicate_titles = _find_duplicates([p.get("title") for p in pages if p.get("title")])
        duplicate_meta = _find_duplicates([s.get("meta_description") for s in seo_data if s.get("meta_description")])

        # Title length issues
        title_too_short = [s for s in seo_data if s.get("title_length") and s.get("title_length") < 30]
        title_too_long = [s for s in seo_data if s.get("title_length") and s.get("title_length") > 60]

        # Meta description length issues
        meta_too_short = [s for s in seo_data if s.get("meta_description_length") and s.get("meta_description_length") < 120]
        meta_too_long = [s for s in seo_data if s.get("meta_description_length") and s.get("meta_description_length") > 160]

        # --- Link Analysis ---
        internal_links = [l for l in links if l.get("link_type") == "internal"]
        external_links = [l for l in links if l.get("link_type") == "external"]
        broken_links = [l for l in links if l.get("is_broken") or (l.get("status_code") and l.get("status_code") >= 400)]
        nav_links = [l for l in links if l.get("is_navigation")]

        # --- Image Analysis ---
        images_missing_alt = [img for img in images if not img.get("alt_text")]
        images_with_alt = [img for img in images if img.get("alt_text")]
        total_image_alt_missing = sum(s.get("image_alt_missing_count", 0) for s in seo_data)

        # --- Issue Breakdown ---
        issues_by_severity = {
            "critical": [i for i in issues if i.get("severity") == "critical"],
            "high": [i for i in issues if i.get("severity") == "high"],
            "medium": [i for i in issues if i.get("severity") == "medium"],
            "low": [i for i in issues if i.get("severity") == "low"],
        }

        issues_by_type = {}
        for issue in issues:
            issue_type = issue.get("type", "Unknown")
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)

        top_issues = [
            {
                "type": k,
                "count": len(v),
                "severity": v[0].get("severity") if v else "unknown",
                "sample_message": v[0].get("message")[:200] if v and v[0].get("message") else None
            }
            for k, v in sorted(issues_by_type.items(), key=lambda x: -len(x[1]))
        ][:15]

        # --- Top Pages Analysis ---
        # Pages with best SEO scores
        top_seo_pages = sorted(
            [p for p in pages if p.get("seo_score")],
            key=lambda x: x.get("seo_score", 0),
            reverse=True
        )[:5]

        # Most linked-to pages (highest internal links)
        most_linked_pages = sorted(
            [p for p in pages if p.get("internal_links")],
            key=lambda x: x.get("internal_links", 0),
            reverse=True
        )[:5]

        # Primary/important pages
        primary_pages = [p for p in pages if p.get("is_primary") or p.get("nav_score", 0) >= 10]

        # --- Internal Linking Analysis ---
        from urllib.parse import urlparse

        # Build URL → page mapping (normalize trailing slashes)
        def normalize_url(url: str) -> str:
            return url.rstrip("/") if url else ""

        page_url_map = {}  # normalized URL → page dict
        page_id_map = {}   # page_id → page dict
        for p in pages:
            page_url_map[normalize_url(p.get("url", ""))] = p
            page_id_map[p.get("id")] = p

        # Determine root URL
        crawl_url = crawl.get("url", "")
        root_normalized = normalize_url(crawl_url)

        # Build inbound/outbound counts from actual link data
        inbound_counts = {normalize_url(p.get("url", "")): 0 for p in pages}
        outbound_counts = {normalize_url(p.get("url", "")): 0 for p in pages}

        for link in internal_links:
            target_norm = normalize_url(link.get("target_url", ""))
            source_page = page_id_map.get(link.get("source_page_id"))
            source_norm = normalize_url(source_page.get("url", "")) if source_page else None

            if target_norm in inbound_counts:
                inbound_counts[target_norm] += 1
            if source_norm and source_norm in outbound_counts:
                outbound_counts[source_norm] += 1

        # Identify orphan pages (0 inbound internal links, excluding root)
        orphan_pages_list = []
        for page in pages:
            page_norm = normalize_url(page.get("url", ""))
            if page_norm == root_normalized:
                continue
            if inbound_counts.get(page_norm, 0) == 0:
                orphan_pages_list.append({
                    "url": page.get("url"),
                    "title": page.get("title", "Untitled"),
                    "depth": page.get("depth", 0),
                })

        # Depth distribution
        depth_dist = {}
        for page in pages:
            d = page.get("depth", 0)
            key = str(d) if d < 3 else "3+"
            depth_dist[key] = depth_dist.get(key, 0) + 1

        # Page linking details (sorted by inbound descending)
        linking_details = []
        for page in pages:
            page_norm = normalize_url(page.get("url", ""))
            linking_details.append({
                "url": page.get("url"),
                "title": page.get("title", "Untitled"),
                "inbound": inbound_counts.get(page_norm, 0),
                "outbound": outbound_counts.get(page_norm, 0),
                "depth": page.get("depth", 0),
            })
        linking_details.sort(key=lambda x: x["inbound"], reverse=True)

        # Most/least linked (top 5 each)
        most_linked_internal = linking_details[:5]
        least_linked_internal = sorted(
            [d for d in linking_details if normalize_url(d["url"]) != root_normalized],
            key=lambda x: x["inbound"]
        )[:5]

        # Calculate linking score (0-100)
        linking_score = 100
        if total_pages > 1:
            # Penalize orphan pages: -15 per orphan, max -40
            orphan_penalty = min(40, len(orphan_pages_list) * 15)
            linking_score -= orphan_penalty

            # Penalize deep pages (3+ clicks): -5 per page, max -20
            deep_pages = [p for p in pages if (p.get("depth", 0) or 0) >= 3]
            deep_penalty = min(20, len(deep_pages) * 5)
            linking_score -= deep_penalty

            # Penalize concentration: if top page (excl. root) gets >50% of all inbound
            non_root_inbound = {k: v for k, v in inbound_counts.items() if k != root_normalized}
            total_non_root_inbound = sum(non_root_inbound.values())
            if total_non_root_inbound > 0 and non_root_inbound:
                max_inbound = max(non_root_inbound.values())
                concentration_ratio = max_inbound / total_non_root_inbound
                if concentration_ratio > 0.5:
                    linking_score -= min(20, int((concentration_ratio - 0.5) * 40))

            # Penalize pages with 0 outbound internal links (dead ends), excl non-HTML
            dead_end_pages = [
                d for d in linking_details
                if d["outbound"] == 0 and normalize_url(d["url"]) != root_normalized
            ]
            dead_end_penalty = min(20, len(dead_end_pages) * 5)
            linking_score -= dead_end_penalty

        linking_score = max(0, linking_score)

        # --- Problem Pages ---
        problem_pages = []
        for page in pages:
            problems = []
            if page.get("status_code") and page.get("status_code") >= 400:
                problems.append(f"HTTP {page.get('status_code')}")
            if page.get("word_count") and page.get("word_count") < 300:
                problems.append("Thin content")
            if not page.get("title") or page.get("title") == "No title found":
                problems.append("Missing title")
            if page.get("response_time") and page.get("response_time") > 3000:
                problems.append("Slow load time")

            if problems:
                problem_pages.append({
                    "url": page.get("url"),
                    "title": page.get("title"),
                    "problems": problems,
                    "problem_count": len(problems)
                })

        problem_pages = sorted(problem_pages, key=lambda x: x["problem_count"], reverse=True)[:10]

        # =============================================
        # PHASE 3: DATA-DRIVEN FINDINGS (Python computes, no LLM)
        # =============================================

        # Per-page audit: grade every page on every SEO dimension
        page_audits = []
        for page in pages:
            page_id = page.get("id")
            seo = seo_map.get(page_id, {})
            page_url = page.get("url", "")
            page_issues_list = [i for i in issues if i.get("page_id") == page_id]
            page_broken = [l for l in broken_links if l.get("source_page_id") == page_id or l.get("page_id") == page_id]

            title = page.get("title", "") or ""
            title_len = seo.get("title_length") or len(title)
            meta = seo.get("meta_description") or page.get("meta_description") or ""
            meta_len = seo.get("meta_description_length") or len(meta)
            h1 = seo.get("h1") or ""
            word_count = page.get("word_count") or 0
            resp_time = page.get("response_time") or 0
            status = page.get("status_code") or 0

            # Grade each dimension
            checks = {}
            checks["title"] = {
                "status": "pass" if 30 <= title_len <= 60 else ("missing" if not title else "fail"),
                "value": title,
                "length": title_len,
                "detail": f'"{title}" ({title_len} chars)' if title else "MISSING",
                "target": "30-60 chars",
            }
            checks["meta_description"] = {
                "status": "pass" if 120 <= meta_len <= 160 else ("missing" if not meta else "fail"),
                "value": meta,
                "length": meta_len,
                "detail": f'{meta_len} chars' if meta else "MISSING",
                "target": "120-160 chars",
            }
            checks["h1"] = {
                "status": "pass" if h1 else "missing",
                "value": h1,
            }
            checks["content_depth"] = {
                "status": "pass" if word_count >= 300 else ("thin" if word_count > 0 else "empty"),
                "word_count": word_count,
                "detail": f'{word_count} words' + (" (thin)" if 0 < word_count < 300 else ""),
            }
            checks["response_time"] = {
                "status": "pass" if resp_time < 1000 else ("slow" if resp_time < 3000 else "critical"),
                "ms": round(resp_time),
            }
            checks["status_code"] = {
                "status": "pass" if 200 <= status < 400 else "fail",
                "code": status,
            }

            # Calculate per-page score (0-100)
            score = 100
            if checks["title"]["status"] == "missing": score -= 25
            elif checks["title"]["status"] == "fail": score -= 10
            if checks["meta_description"]["status"] == "missing": score -= 20
            elif checks["meta_description"]["status"] == "fail": score -= 8
            if checks["h1"]["status"] == "missing": score -= 15
            if checks["content_depth"]["status"] == "thin": score -= 10
            elif checks["content_depth"]["status"] == "empty": score -= 20
            if checks["response_time"]["status"] == "slow": score -= 5
            elif checks["response_time"]["status"] == "critical": score -= 15
            if checks["status_code"]["status"] == "fail": score -= 25

            page_audits.append({
                "url": page_url,
                "title": title,
                "score": max(0, score),
                "checks": checks,
                "issue_count": len(page_issues_list),
                "issues": [i.get("message", "") for i in page_issues_list[:5]],
            })

        # Sort by score ascending (worst pages first)
        page_audits.sort(key=lambda x: x["score"])

        # Compute aggregate findings — specific, quantitative
        data_findings = []

        # Title findings
        title_issues = [pa for pa in page_audits if pa["checks"]["title"]["status"] != "pass"]
        if title_issues:
            for pa in title_issues:
                check = pa["checks"]["title"]
                if check["status"] == "missing":
                    data_findings.append({
                        "category": "SEO",
                        "severity": "high",
                        "finding": f'Missing title tag on {pa["url"]}',
                        "current_value": None,
                        "target": "30-60 chars with primary keywords",
                        "url": pa["url"],
                    })
                else:
                    data_findings.append({
                        "category": "SEO",
                        "severity": "medium",
                        "finding": f'Title {"too short" if check["length"] < 30 else "too long"} on {pa["url"]}: {check["detail"]}',
                        "current_value": check["value"],
                        "current_length": check["length"],
                        "target": "30-60 chars",
                        "url": pa["url"],
                    })

        # Meta description findings
        meta_issues = [pa for pa in page_audits if pa["checks"]["meta_description"]["status"] != "pass"]
        if meta_issues:
            for pa in meta_issues:
                check = pa["checks"]["meta_description"]
                if check["status"] == "missing":
                    data_findings.append({
                        "category": "SEO",
                        "severity": "high",
                        "finding": f'Missing meta description on {pa["url"]}',
                        "current_value": None,
                        "target": "120-160 chars",
                        "url": pa["url"],
                    })
                else:
                    data_findings.append({
                        "category": "SEO",
                        "severity": "medium",
                        "finding": f'Meta description {"too short" if check["length"] < 120 else "too long"} on {pa["url"]}: {check["length"]} chars',
                        "current_value": check["value"],
                        "current_length": check["length"],
                        "target": "120-160 chars",
                        "url": pa["url"],
                    })

        # Content depth findings
        thin_pages = [pa for pa in page_audits if pa["checks"]["content_depth"]["status"] in ("thin", "empty")]
        for pa in thin_pages:
            data_findings.append({
                "category": "Content",
                "severity": "medium" if pa["checks"]["content_depth"]["status"] == "thin" else "high",
                "finding": f'{"Thin" if pa["checks"]["content_depth"]["word_count"] > 0 else "Empty"} content on {pa["url"]}: {pa["checks"]["content_depth"]["word_count"]} words',
                "current_value": pa["checks"]["content_depth"]["word_count"],
                "target": "300+ words",
                "url": pa["url"],
            })

        # Performance findings
        slow_pages = [pa for pa in page_audits if pa["checks"]["response_time"]["status"] != "pass"]
        for pa in slow_pages:
            data_findings.append({
                "category": "Performance",
                "severity": "high" if pa["checks"]["response_time"]["status"] == "critical" else "medium",
                "finding": f'Slow response on {pa["url"]}: {pa["checks"]["response_time"]["ms"]}ms',
                "current_value": pa["checks"]["response_time"]["ms"],
                "target": "Under 1000ms",
                "url": pa["url"],
            })

        # Broken link findings
        for bl in broken_links[:15]:
            data_findings.append({
                "category": "Links",
                "severity": "high",
                "finding": f'Broken link: {bl.get("target_url", "?")} (HTTP {bl.get("status_code", "?")})',
                "current_value": bl.get("status_code"),
                "url": bl.get("target_url", ""),
            })

        # Internal linking findings
        for orphan in orphan_pages_list:
            data_findings.append({
                "category": "Links",
                "severity": "high",
                "finding": f'Orphan page (no internal links point to it): {orphan["url"]}',
                "current_value": 0,
                "target": "At least 1 inbound internal link",
                "url": orphan["url"],
            })

        if deep_pages:
            deep_urls = [p.get("url") for p in deep_pages[:5]]
            data_findings.append({
                "category": "Links",
                "severity": "medium",
                "finding": f'{len(deep_pages)} page(s) are 3+ clicks from homepage',
                "current_value": len(deep_pages),
                "target": "All important pages within 2 clicks",
                "url": deep_urls[0] if deep_urls else None,
            })

        if dead_end_pages:
            data_findings.append({
                "category": "Links",
                "severity": "medium",
                "finding": f'{len(dead_end_pages)} page(s) have no outbound internal links (dead ends)',
                "current_value": len(dead_end_pages),
                "target": "Every page should link to related content",
            })

        # Image alt text findings
        if images_missing_alt:
            data_findings.append({
                "category": "Accessibility",
                "severity": "medium",
                "finding": f'{len(images_missing_alt)} of {len(images)} images missing alt text ({round(len(images_missing_alt)/len(images)*100) if images else 0}%)',
                "current_value": len(images_missing_alt),
                "target": "100% alt text coverage",
            })

        # Compute summary stats
        scores = [pa["score"] for pa in page_audits]
        summary_stats = {
            "avg_page_score": round(mean(scores)) if scores else 0,
            "min_page_score": min(scores) if scores else 0,
            "max_page_score": max(scores) if scores else 0,
            "pages_passing": len([s for s in scores if s >= 80]),
            "pages_warning": len([s for s in scores if 50 <= s < 80]),
            "pages_failing": len([s for s in scores if s < 50]),
            "title_pass_rate": round(len([pa for pa in page_audits if pa["checks"]["title"]["status"] == "pass"]) / total_pages * 100) if total_pages else 0,
            "meta_pass_rate": round(len([pa for pa in page_audits if pa["checks"]["meta_description"]["status"] == "pass"]) / total_pages * 100) if total_pages else 0,
            "h1_pass_rate": round(len([pa for pa in page_audits if pa["checks"]["h1"]["status"] == "pass"]) / total_pages * 100) if total_pages else 0,
            "content_pass_rate": round(len([pa for pa in page_audits if pa["checks"]["content_depth"]["status"] == "pass"]) / total_pages * 100) if total_pages else 0,
            "performance_pass_rate": round(len([pa for pa in page_audits if pa["checks"]["response_time"]["status"] == "pass"]) / total_pages * 100) if total_pages else 0,
            "total_findings": len(data_findings),
            "findings_by_severity": {
                "high": len([f for f in data_findings if f["severity"] == "high"]),
                "medium": len([f for f in data_findings if f["severity"] == "medium"]),
                "low": len([f for f in data_findings if f.get("severity") == "low"]),
            },
        }

        # =============================================
        # PHASE 3.5: SEMANTIC STRATEGY ANALYSIS (CRO layer)
        # =============================================
        import asyncio

        semantic_strategy_results = []
        strategy_summary_text = ""

        try:
            # Select top pages for strategy analysis (primary pages or high nav_score, max 10)
            strategy_candidates = [
                p for p in pages
                if p.get("is_primary") or p.get("nav_score", 0) >= 10
            ]
            if not strategy_candidates:
                # Fallback: use pages with highest word count (most content to analyze)
                strategy_candidates = sorted(
                    [p for p in pages if p.get("word_count", 0) > 100],
                    key=lambda x: x.get("word_count", 0),
                    reverse=True,
                )
            strategy_candidates = strategy_candidates[:10]

            # Fetch HTML paths for candidates (separate query to avoid breaking Phase 1)
            # NOTE: Production DB may have the column as html_snapshot_path or html_storage_path
            # (migration says html_storage_path, crawler writes html_snapshot_path) — check both
            from app.services.storage import get_file_content

            candidate_ids = [p.get("id") for p in strategy_candidates if p.get("id")]
            html_paths = {}
            if candidate_ids:
                try:
                    html_response = supabase_client.table("pages").select("*").in_(
                        "id", candidate_ids
                    ).execute()
                    for r in (html_response.data or []):
                        path = r.get("html_storage_path") or r.get("html_snapshot_path")
                        if path:
                            html_paths[r["id"]] = path
                    logger.info(f"Strategy: found HTML paths for {len(html_paths)}/{len(candidate_ids)} pages")
                except Exception as e:
                    logger.warning(f"Could not fetch HTML paths for strategy: {e}")

            skeletons = []
            for page in strategy_candidates:
                page_id = page.get("id")
                html_path = html_paths.get(page_id)
                if not html_path:
                    logger.debug(f"Strategy: no HTML path for {page.get('url')} (id={page_id})")
                    continue

                try:
                    file_content = await get_file_content(html_path)
                    if file_content:
                        html_content = file_content.decode("utf-8", errors="replace")
                        skeleton = build_semantic_skeleton(page, html_content)
                        if skeleton:
                            skeletons.append(skeleton)
                        else:
                            logger.debug(f"Strategy: skeleton empty for {page.get('url')}")
                    else:
                        logger.debug(f"Strategy: file not found at {html_path} for {page.get('url')}")
                except Exception as e:
                    logger.warning(f"Strategy: error loading HTML for {page.get('url')}: {e}")
                    continue

            logger.info(f"Strategy: built {len(skeletons)} skeletons from {len(strategy_candidates)} candidates")

            # Run LLM strategy calls in parallel
            if skeletons:
                # Build site-wide voice fingerprint so AI scores consistency
                # with the detected voice, not against a generic CRO template
                voice_fp = build_voice_fingerprint(skeletons)
                logger.info(f"Strategy: voice fingerprint — {voice_fp.get('voice_person')}, {voice_fp.get('tone_formality')}, cta_style={voice_fp.get('cta_style')}, trust_first={voice_fp.get('trust_first_positioning')}")

                llm_service = LLMService(crawl_id=crawl_id)
                strategy_tasks = [
                    llm_service.analyze_page_strategy(skeleton, voice_fingerprint=voice_fp)
                    for skeleton in skeletons
                ]
                raw_results = await asyncio.gather(*strategy_tasks, return_exceptions=True)

                for skeleton, result in zip(skeletons, raw_results):
                    if isinstance(result, Exception):
                        logger.warning(f"Strategy analysis failed for {skeleton['url']}: {result}")
                        continue

                    # Validation: check suggested title/meta lengths
                    strategy_dict = result.model_dump()
                    if strategy_dict.get("suggested_title"):
                        title_len = len(strategy_dict["suggested_title"])
                        if title_len < 20 or title_len > 80:
                            strategy_dict["suggested_title"] = None
                    if strategy_dict.get("suggested_meta"):
                        meta_len = len(strategy_dict["suggested_meta"])
                        if meta_len < 100 or meta_len > 200:
                            strategy_dict["suggested_meta"] = None

                    semantic_strategy_results.append({
                        "url": skeleton["url"],
                        "purpose": skeleton["inferred_purpose"],
                        "language": skeleton.get("language", "en"),
                        "analysis": strategy_dict,
                    })

                # Build strategy summary for executive summary prompt
                if semantic_strategy_results:
                    strategy_lines = []
                    scores = [r["analysis"]["overall_strategy_score"] for r in semantic_strategy_results]
                    avg_score = round(sum(scores) / len(scores))
                    strategy_lines.append(f"Avg strategy score: {avg_score}/100 across {len(semantic_strategy_results)} pages")
                    for r in semantic_strategy_results[:5]:
                        a = r["analysis"]
                        strategy_lines.append(
                            f"  {r['url']} ({r['purpose']}): strategy {a['overall_strategy_score']}/100 — "
                            f"intent {a['intent_gap']['alignment_score']}, tone {a['tone_audit']['tone_match_score']}, skim {a['skim_test']['skim_score']}. "
                            f"Top rec: {a['top_recommendation'][:100]}"
                        )
                    strategy_summary_text = "\n".join(strategy_lines)

        except Exception as e:
            logger.warning(f"Semantic strategy phase failed (non-fatal): {e}")

        # =============================================
        # PHASE 4: AI NARRATIVE (narrates the data, doesn't analyze)
        # =============================================

        # Build the data analysis summary for the AI to narrate
        findings_text = "\n".join([
            f"- [{f['severity'].upper()}] {f['finding']}"
            for f in data_findings[:25]
        ])

        site_data = {
            "base_url": crawl.get("url", ""),
            "total_pages": total_pages,
            "total_issues": len(issues),
            "summary_stats": summary_stats,
            "data_findings": findings_text,
            "page_audits_summary": "\n".join([
                f"  {pa['url']}: score {pa['score']}/100, {pa['issue_count']} issues"
                + (f" — {', '.join(pa['issues'][:2])}" if pa['issues'] else "")
                for pa in page_audits[:15]
            ]),
            "broken_links": len(broken_links),
            "missing_meta": len(missing_meta_desc),
            "thin_content_pages": len(thin_content_pages),
            "images_missing_alt": len(images_missing_alt),
            "total_images": len(images),
            "avg_response_time_ms": avg_response_time,
            "status_code_summary": {
                "2xx": len(status_2xx),
                "3xx": len(status_3xx),
                "4xx": len(status_4xx),
                "5xx": len(status_5xx),
            },
            "top_issues": top_issues,
        }

        # Include strategy findings in executive summary context if available
        if strategy_summary_text:
            site_data["strategy_findings"] = strategy_summary_text

        # Reuse llm_service if it was created in Phase 3.5, otherwise create new
        if not semantic_strategy_results:
            llm_service = LLMService(crawl_id=crawl_id)
        executive_summary = await llm_service.generate_executive_summary(site_data)

        # =============================================
        # PHASE 4: BUILD COMPREHENSIVE REPORT
        # =============================================

        crawl_duration_seconds = None
        if crawl.get("created_at") and crawl.get("completed_at"):
            try:
                from datetime import datetime as dt
                start = dt.fromisoformat(crawl.get("created_at").replace("Z", "+00:00"))
                end = dt.fromisoformat(crawl.get("completed_at").replace("Z", "+00:00"))
                crawl_duration_seconds = int((end - start).total_seconds())
            except Exception:
                pass

        report = {
            "report_version": "2.0",
            "crawl_id": crawl_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),

            # --- Site Overview ---
            "site_overview": {
                "url": crawl.get("url"),
                "name": crawl.get("name"),
                "crawl_started": crawl.get("created_at"),
                "crawl_completed": crawl.get("completed_at"),
                "crawl_duration_seconds": crawl_duration_seconds,
                "max_pages_setting": crawl.get("max_pages"),
                "max_depth_setting": crawl.get("max_depth"),
            },

            # --- Executive Summary (AI-Generated narrative) ---
            "executive_summary": executive_summary.model_dump(),

            # --- Data-Driven Findings (Python-computed, no LLM) ---
            "data_findings": data_findings,
            "page_audits": page_audits,
            "summary_stats": summary_stats,

            # --- Metrics (consumed by frontend Crawl Metrics widget) ---
            "metrics": {
                "total_pages": total_pages,
                "total_issues": len(issues),
                "broken_links": len(broken_links),
                "missing_meta": len(missing_meta_desc),
                "thin_content_pages": len(thin_content_pages),
                "critical_issues": len(issues_by_severity["critical"]),
                "high_issues": len(issues_by_severity["high"]),
            },

            # --- Overall Health Metrics ---
            "health_metrics": {
                "total_pages_crawled": total_pages,
                "total_issues_found": len(issues),
                "critical_issues": len(issues_by_severity["critical"]),
                "high_issues": len(issues_by_severity["high"]),
                "medium_issues": len(issues_by_severity["medium"]),
                "low_issues": len(issues_by_severity["low"]),
                "health_score": executive_summary.site_health_score,
            },

            # --- Status Code Breakdown ---
            "status_codes": {
                "successful_2xx": len(status_2xx),
                "redirects_3xx": len(status_3xx),
                "client_errors_4xx": len(status_4xx),
                "server_errors_5xx": len(status_5xx),
                "success_rate_percent": round((len(status_2xx) / total_pages * 100), 1) if total_pages > 0 else 0,
            },

            # --- Performance Metrics ---
            "performance": {
                "avg_response_time_ms": avg_response_time,
                "median_response_time_ms": median_response_time,
                "avg_page_size_kb": avg_page_size,
                "slowest_pages": [
                    {
                        "url": p.get("url"),
                        "title": p.get("title"),
                        "response_time_ms": p.get("response_time")
                    }
                    for p in slowest_pages
                ],
                "largest_pages": [
                    {
                        "url": p.get("url"),
                        "title": p.get("title"),
                        "size_kb": round((p.get("page_size_bytes") or 0) / 1024, 2)
                    }
                    for p in largest_pages
                ],
            },

            # --- Content Analysis ---
            "content": {
                "avg_word_count": avg_word_count,
                "thin_content_pages_count": len(thin_content_pages),
                "content_rich_pages_count": len(content_rich_pages),
                "thin_content_pages": [
                    {
                        "url": p.get("url"),
                        "title": p.get("title"),
                        "word_count": p.get("word_count")
                    }
                    for p in thin_content_pages[:10]
                ],
            },

            # --- SEO Analysis ---
            "seo": {
                "pages_missing_title": len(missing_title),
                "pages_missing_meta_description": len(missing_meta_desc),
                "pages_missing_h1": len(missing_h1),
                "duplicate_titles_count": len(duplicate_titles),
                "duplicate_meta_descriptions_count": len(duplicate_meta),
                "title_too_short_count": len(title_too_short),
                "title_too_long_count": len(title_too_long),
                "meta_too_short_count": len(meta_too_short),
                "meta_too_long_count": len(meta_too_long),
                "duplicate_titles": duplicate_titles[:10],
                "duplicate_meta_descriptions": duplicate_meta[:10],
                "top_seo_pages": [
                    {
                        "url": p.get("url"),
                        "title": p.get("title"),
                        "seo_score": p.get("seo_score")
                    }
                    for p in top_seo_pages
                ],
            },

            # --- Link Analysis ---
            "links": {
                "total_links": len(links),
                "internal_links": len(internal_links),
                "external_links": len(external_links),
                "broken_links": len(broken_links),
                "navigation_links": len(nav_links),
                "broken_links_list": [
                    {
                        "url": l.get("target_url"),
                        "status_code": l.get("status_code"),
                        "anchor_text": l.get("anchor_text")
                    }
                    for l in broken_links[:20]
                ],
            },

            # --- Internal Linking Analysis ---
            "internal_linking": {
                "linking_score": linking_score,
                "total_internal_links": len(internal_links),
                "orphan_pages": orphan_pages_list,
                "orphan_count": len(orphan_pages_list),
                "dead_end_count": len(dead_end_pages),
                "most_linked": most_linked_internal,
                "least_linked": least_linked_internal,
                "depth_distribution": depth_dist,
                "page_details": linking_details,
            },

            # --- Image Analysis ---
            "images": {
                "total_images": len(images),
                "images_missing_alt": len(images_missing_alt),
                "images_with_alt": len(images_with_alt),
                "alt_text_coverage_percent": round((len(images_with_alt) / len(images) * 100), 1) if images else 100,
            },

            # --- Issues Breakdown ---
            "issues": {
                "by_severity": {
                    "critical": len(issues_by_severity["critical"]),
                    "high": len(issues_by_severity["high"]),
                    "medium": len(issues_by_severity["medium"]),
                    "low": len(issues_by_severity["low"]),
                },
                "top_issues": top_issues,
            },

            # --- Pages Needing Attention ---
            "problem_pages": problem_pages,

            # --- Top Performing Pages ---
            "top_pages": {
                "by_seo_score": [
                    {
                        "url": p.get("url"),
                        "title": p.get("title"),
                        "seo_score": p.get("seo_score")
                    }
                    for p in top_seo_pages
                ],
                "most_linked": [
                    {
                        "url": p.get("url"),
                        "title": p.get("title"),
                        "internal_links": p.get("internal_links")
                    }
                    for p in most_linked_pages
                ],
                "primary_pages_count": len(primary_pages),
            },

            # --- Semantic Strategy (CRO Analysis) ---
            "semantic_strategy": {
                "page_analyses": semantic_strategy_results,
                "avg_strategy_score": round(
                    sum(r["analysis"]["overall_strategy_score"] for r in semantic_strategy_results) / len(semantic_strategy_results)
                ) if semantic_strategy_results else None,
                "pages_analyzed": len(semantic_strategy_results),
            } if semantic_strategy_results else None,

            # --- LLM Usage ---
            "llm_usage": llm_service.get_usage_summary(),
        }

        # =============================================
        # PHASE 5: STORE REPORT
        # =============================================

        update_response = supabase_client.table("crawls").update({
            "ai_report": report,
            "ai_report_generated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", crawl_id).execute()

        if hasattr(update_response, "error") and update_response.error:
            logger.error(f"Failed to store report: {update_response.error}")

        return report

    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=f"LLM feature disabled: {e}")
    except BudgetExceededError as e:
        raise HTTPException(status_code=402, detail=f"Budget exceeded: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _find_duplicates(items: List[str]) -> List[Dict[str, Any]]:
    """Find duplicate items and return them with counts."""
    from collections import Counter
    counts = Counter(items)
    return [
        {"value": item, "count": count}
        for item, count in counts.items()
        if count > 1
    ][:10]


@router.get("/crawl/{crawl_id}/report")
async def get_crawl_report(
    crawl_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the stored AI report for a crawl.

    Returns the previously generated report, or 404 if not generated yet.
    """
    from supabase import create_client
    from app.core.config import settings

    # Use service role client to bypass RLS
    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    try:
        response = supabase_client.table("crawls").select(
            "id, name, url, user_id, ai_report, ai_report_generated_at"
        ).eq("id", crawl_id).single().execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Security check: verify user owns this crawl
        if str(response.data.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to access this crawl")

        crawl = response.data

        if not crawl.get("ai_report"):
            raise HTTPException(
                status_code=404,
                detail="Report not generated yet. Use POST to generate a report."
            )

        return {
            "crawl_id": crawl_id,
            "crawl_name": crawl.get("name"),
            "site_url": crawl.get("url"),
            "generated_at": crawl.get("ai_report_generated_at"),
            "report": crawl.get("ai_report"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawl/{crawl_id}/report/export/pdf")
async def export_report_pdf(
    crawl_id: str,
    current_user: User = Depends(get_current_user)
):
    """Export the crawl report as a branded PDF."""
    from supabase import create_client
    from app.core.config import settings
    from app.services.report_export import generate_pdf_report

    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    try:
        response = supabase_client.table("crawls").select(
            "id, name, url, user_id, ai_report, ai_report_generated_at"
        ).eq("id", crawl_id).single().execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        if str(response.data.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        crawl = response.data
        report_data = crawl.get("ai_report")
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not generated yet")

        pdf_bytes = generate_pdf_report(report_data, crawl)
        site_name = crawl.get("url", "site").replace("https://", "").replace("http://", "").replace("/", "_")
        filename = f"cushlabs_report_{site_name}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawl/{crawl_id}/report/export/csv")
async def export_report_csv(
    crawl_id: str,
    export_type: str = Query("page_audits", regex="^(page_audits|findings)$"),
    current_user: User = Depends(get_current_user)
):
    """Export report data as CSV (page_audits or findings)."""
    from supabase import create_client
    from app.core.config import settings
    from app.services.report_export import generate_csv_export

    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    try:
        response = supabase_client.table("crawls").select(
            "id, name, url, user_id, ai_report"
        ).eq("id", crawl_id).single().execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        if str(response.data.get("user_id")) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        report_data = response.data.get("ai_report")
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not generated yet")

        csv_content = generate_csv_export(report_data, export_type)
        site_name = response.data.get("url", "site").replace("https://", "").replace("http://", "").replace("/", "_")
        filename = f"cushlabs_{export_type}_{site_name}.csv"

        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawl/{crawl_id}/usage")
async def get_crawl_usage(crawl_id: str):
    """
    Get LLM usage statistics for a crawl.
    """
    # TODO: Implement database lookup
    return {
        "crawl_id": crawl_id,
        "message": "Usage tracking requires database integration."
    }


# =========================================
# Specific Analysis Endpoints
# =========================================

@router.post("/content-quality")
async def analyze_content_quality(
    url: str,
    content: str,
    title: Optional[str] = None,
    page_type: Optional[str] = None,
):
    """
    Get detailed content quality analysis for a page.
    """
    try:
        service = LLMService(crawl_id="api_request")
        
        result = await service.analyze_content_quality(
            content=content,
            url=url,
            title=title,
            page_type=page_type
        )
        
        return {
            "analysis": result.model_dump(),
            "usage": service.get_usage_summary()
        }
        
    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Content quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seo-recommendations")
async def get_seo_recommendations(
    url: str,
    content: str,
    title: Optional[str] = None,
    meta_description: Optional[str] = None,
    h1: Optional[str] = None,
    word_count: int = 0,
):
    """
    Get SEO recommendations for a page.
    """
    try:
        service = LLMService(crawl_id="api_request")
        
        result = await service.generate_seo_recommendations(
            content=content,
            url=url,
            title=title,
            meta_description=meta_description,
            h1=h1,
            word_count=word_count
        )
        
        return {
            "recommendations": result.model_dump(),
            "usage": service.get_usage_summary()
        }
        
    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"SEO analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meta-description")
async def generate_meta_description(
    url: str,
    title: str,
    content: str,
):
    """
    Generate an optimized meta description for a page.
    """
    try:
        service = LLMService(crawl_id="api_request")
        
        result = await service.generate_meta_description(
            content=content,
            title=title,
            url=url
        )
        
        return {
            "suggestion": result.model_dump(),
            "usage": service.get_usage_summary()
        }
        
    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Meta description generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categorize")
async def categorize_page(
    url: str,
    content: str,
    title: Optional[str] = None,
):
    """
    Categorize a page by type.
    """
    try:
        service = LLMService(crawl_id="api_request")
        
        result = await service.categorize_page(
            content=content,
            url=url,
            title=title
        )
        
        return {
            "categorization": result.model_dump(),
            "usage": service.get_usage_summary()
        }
        
    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Page categorization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-topics")
async def extract_topics(
    url: str,
    content: str,
    title: Optional[str] = None,
):
    """
    Extract topics and keywords from a page.
    """
    try:
        service = LLMService(crawl_id="api_request")
        
        result = await service.extract_topics(
            content=content,
            url=url,
            title=title
        )
        
        return {
            "topics": result.model_dump(),
            "usage": service.get_usage_summary()
        }
        
    except TaskDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Topic extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# Image Analysis Data Retrieval
# =========================================

@router.get("/crawl/{crawl_id}/images")
async def get_crawl_images(crawl_id: str):
    """
    Get all image analysis results for a crawl.
    
    Returns images with their current and suggested alt text.
    """
    try:
        from app.db.supabase import supabase_client
        
        # Fetch image analysis data
        result = supabase_client.table("image_analysis").select(
            "id, page_id, crawl_id, src_url, current_alt_text, suggested_alt_text, "
            "is_decorative, confidence, context, created_at"
        ).eq("crawl_id", crawl_id).order("created_at", desc=True).execute()
        
        images = result.data if result.data else []
        
        # Fetch associated page info
        if images:
            page_ids = list(set(img["page_id"] for img in images if img.get("page_id")))
            if page_ids:
                pages_result = supabase_client.table("pages").select(
                    "id, url, title"
                ).in_("id", page_ids).execute()
                
                pages = {p["id"]: p for p in (pages_result.data or [])}
            else:
                pages = {}
        else:
            pages = {}
        
        return {
            "images": images,
            "pages": list(pages.values()),
            "total_count": len(images),
            "missing_alt_count": len([img for img in images if not img.get("current_alt")]),
            "poor_quality_count": len([img for img in images if img.get("confidence", 1.0) < 0.7])
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch image analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))