"""
Analysis API Routes

Endpoints for triggering LLM-powered content analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from app.services.llm_service import LLMService, TaskDisabledError, BudgetExceededError
from app.services.content_analyzer import ContentAnalyzer, quick_analyze_url
from app.core.llm_config import get_llm_settings, LLMTask, get_task_config, is_task_enabled

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
async def generate_crawl_report(crawl_id: str):
    """
    Generate an executive report for a completed crawl.
    
    Requires the crawl to have page analyses completed.
    """
    # TODO: Implement database integration to fetch crawl data
    # For now, return a placeholder
    
    return {
        "status": "not_implemented",
        "message": "Report generation requires database integration. Coming soon."
    }


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