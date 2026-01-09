"""
Content Analyzer Service

High-level service for analyzing crawled content using LLM.
This service orchestrates different types of analysis and
provides convenient methods for common use cases.

Usage:
    analyzer = ContentAnalyzer(crawl_id="abc123")
    
    # Analyze single page
    result = await analyzer.analyze_page(page_data)
    
    # Analyze entire crawl
    report = await analyzer.generate_crawl_report(crawl_data)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.llm_service import (
    LLMService,
    LLMServiceError,
    TaskDisabledError,
    BudgetExceededError,
)
from app.models.llm_models import (
    PageSummary,
    PageCategorization,
    TopicExtraction,
    ContentQualityAnalysis,
    SEOAnalysis,
    ExecutiveSummary,
    BrandVoiceAnalysis,
    ContentStrategyAnalysis,
)

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    High-level content analysis orchestrator.
    
    Provides convenient methods for analyzing pages and crawls,
    handling errors gracefully, and batching operations.
    """
    
    def __init__(
        self,
        crawl_id: str,
        llm_service: Optional[LLMService] = None
    ):
        self.crawl_id = crawl_id
        self.llm_service = llm_service or LLMService(crawl_id=crawl_id)
        self._analysis_cache: Dict[str, Any] = {}
    
    async def analyze_page_basic(
        self,
        url: str,
        content: str,
        title: Optional[str] = None,
        meta_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform basic (Tier 1) analysis on a page.
        Fast and cheap - suitable for running during crawl.
        
        Returns:
            Dict with summary, category, and topics
        """
        results = {
            "url": url,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "analysis_tier": 1,
            "summary": None,
            "category": None,
            "topics": None,
            "errors": [],
        }
        
        # Run analyses in parallel
        tasks = []
        
        # Summary
        tasks.append(self._safe_analyze(
            "summary",
            self.llm_service.analyze_page_summary(content, url, title)
        ))
        
        # Categorization
        tasks.append(self._safe_analyze(
            "category",
            self.llm_service.categorize_page(content, url, title)
        ))
        
        # Topics
        tasks.append(self._safe_analyze(
            "topics",
            self.llm_service.extract_topics(content, url, title)
        ))
        
        # Wait for all
        analysis_results = await asyncio.gather(*tasks)
        
        # Process results
        for key, result, error in analysis_results:
            if error:
                results["errors"].append({"type": key, "error": str(error)})
            else:
                results[key] = result.model_dump() if result else None
        
        return results
    
    async def analyze_page_detailed(
        self,
        url: str,
        content: str,
        title: Optional[str] = None,
        meta_description: Optional[str] = None,
        h1: Optional[str] = None,
        word_count: int = 0,
        page_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform detailed (Tier 1 + Tier 2) analysis on a page.
        More comprehensive but more expensive.
        
        Returns:
            Dict with all analysis results
        """
        # Start with basic analysis
        results = await self.analyze_page_basic(url, content, title, meta_description)
        results["analysis_tier"] = 2
        
        # Add detailed analyses
        detail_tasks = []
        
        # Content quality
        detail_tasks.append(self._safe_analyze(
            "content_quality",
            self.llm_service.analyze_content_quality(
                content, url, title, page_type
            )
        ))
        
        # SEO recommendations
        detail_tasks.append(self._safe_analyze(
            "seo_analysis",
            self.llm_service.generate_seo_recommendations(
                content, url, title, meta_description, h1, word_count
            )
        ))
        
        # Meta description suggestion if missing
        if not meta_description and title:
            detail_tasks.append(self._safe_analyze(
                "meta_suggestion",
                self.llm_service.generate_meta_description(content, title, url)
            ))
        
        # Wait for detail analyses
        detail_results = await asyncio.gather(*detail_tasks)
        
        for key, result, error in detail_results:
            if error:
                results["errors"].append({"type": key, "error": str(error)})
            else:
                results[key] = result.model_dump() if result else None
        
        return results
    
    async def analyze_page_full(
        self,
        url: str,
        content: str,
        title: Optional[str] = None,
        meta_description: Optional[str] = None,
        h1: Optional[str] = None,
        word_count: int = 0,
        page_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform full analysis including all tiers.
        Most comprehensive, highest cost.
        """
        results = await self.analyze_page_detailed(
            url, content, title, meta_description, h1, word_count, page_type
        )
        results["analysis_tier"] = "full"
        
        # Title quality assessment
        if title:
            key, result, error = await self._safe_analyze(
                "title_quality",
                self.llm_service.assess_title_quality(
                    title,
                    meta_description,
                    content[:1500],
                    url
                )
            )
            if error:
                results["errors"].append({"type": key, "error": str(error)})
            else:
                results[key] = result.model_dump() if result else None
        
        return results
    
    async def analyze_images_batch(
        self,
        images: List[Dict[str, Any]],
        page_content: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate alt text suggestions for multiple images.
        
        Args:
            images: List of image dicts with 'src_url', 'alt_text', 'surrounding_text'
            page_content: Content of the page for context
        
        Returns:
            List of image dicts with added 'suggested_alt' field
        """
        results = []
        
        # Only process images without good alt text
        images_needing_alt = [
            img for img in images
            if not img.get("alt_text") or len(img.get("alt_text", "")) < 5
        ]
        
        # Limit batch size
        batch_size = 20
        images_to_process = images_needing_alt[:batch_size]
        
        for image in images_to_process:
            try:
                suggestion = await self.llm_service.suggest_alt_text(
                    surrounding_text=image.get("surrounding_text", ""),
                    image_filename=image.get("src_url", "").split("/")[-1],
                    page_context=page_content[:500]
                )
                
                results.append({
                    "src_url": image.get("src_url"),
                    "current_alt": image.get("alt_text"),
                    "suggested_alt": suggestion.suggested_alt_text,
                    "is_decorative": suggestion.is_decorative,
                    "confidence": suggestion.confidence,
                })
                
            except Exception as e:
                logger.warning(f"Failed to generate alt text for {image.get('src_url')}: {e}")
                results.append({
                    "src_url": image.get("src_url"),
                    "error": str(e)
                })
        
        return results
    
    async def generate_crawl_report(
        self,
        crawl_data: Dict[str, Any],
        page_analyses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report for a completed crawl.
        
        This is the main Tier 3 synthesis operation.
        """
        report = {
            "crawl_id": self.crawl_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "executive_summary": None,
            "content_strategy": None,
            "brand_voice": None,
            "usage_summary": None,
            "errors": [],
        }
        
        # Prepare data for synthesis
        site_data = self._prepare_site_data(crawl_data, page_analyses)
        
        # Generate executive summary
        try:
            exec_summary = await self.llm_service.generate_executive_summary(site_data)
            report["executive_summary"] = exec_summary.model_dump()
        except TaskDisabledError:
            logger.info("Executive summary disabled")
        except BudgetExceededError as e:
            report["errors"].append({"type": "executive_summary", "error": str(e)})
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            report["errors"].append({"type": "executive_summary", "error": str(e)})
        
        # Generate content strategy (if budget allows)
        try:
            page_inventory = self._prepare_page_inventory(page_analyses)
            content_strategy = await self.llm_service.generate_content_strategy(
                site_data, page_inventory
            )
            report["content_strategy"] = content_strategy.model_dump()
        except (TaskDisabledError, BudgetExceededError) as e:
            logger.info(f"Content strategy skipped: {e}")
        except Exception as e:
            logger.error(f"Failed to generate content strategy: {e}")
            report["errors"].append({"type": "content_strategy", "error": str(e)})
        
        # Brand voice analysis (if budget allows)
        try:
            page_samples = self._prepare_page_samples(page_analyses)
            if len(page_samples) >= 3:
                brand_voice = await self.llm_service.analyze_brand_voice(
                    page_samples,
                    crawl_data.get("base_url", "")
                )
                report["brand_voice"] = brand_voice.model_dump()
        except (TaskDisabledError, BudgetExceededError) as e:
            logger.info(f"Brand voice analysis skipped: {e}")
        except Exception as e:
            logger.error(f"Failed to analyze brand voice: {e}")
            report["errors"].append({"type": "brand_voice", "error": str(e)})
        
        # Add usage summary
        report["usage_summary"] = self.llm_service.get_usage_summary()
        
        return report
    
    async def batch_analyze_pages(
        self,
        pages: List[Dict[str, Any]],
        analysis_level: str = "basic",  # "basic", "detailed", or "full"
        concurrency: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple pages with controlled concurrency.
        
        Args:
            pages: List of page dicts with url, content, title, etc.
            analysis_level: Level of analysis to perform
            concurrency: Max concurrent analyses
        
        Returns:
            List of analysis results
        """
        results = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def analyze_with_limit(page: Dict) -> Dict:
            async with semaphore:
                try:
                    if analysis_level == "basic":
                        return await self.analyze_page_basic(
                            url=page.get("url", ""),
                            content=page.get("content", ""),
                            title=page.get("title"),
                            meta_description=page.get("meta_description"),
                        )
                    elif analysis_level == "detailed":
                        return await self.analyze_page_detailed(
                            url=page.get("url", ""),
                            content=page.get("content", ""),
                            title=page.get("title"),
                            meta_description=page.get("meta_description"),
                            h1=page.get("h1"),
                            word_count=page.get("word_count", 0),
                            page_type=page.get("page_type"),
                        )
                    else:  # full
                        return await self.analyze_page_full(
                            url=page.get("url", ""),
                            content=page.get("content", ""),
                            title=page.get("title"),
                            meta_description=page.get("meta_description"),
                            h1=page.get("h1"),
                            word_count=page.get("word_count", 0),
                            page_type=page.get("page_type"),
                        )
                except BudgetExceededError:
                    return {
                        "url": page.get("url", ""),
                        "error": "Budget exceeded",
                        "skipped": True
                    }
                except Exception as e:
                    return {
                        "url": page.get("url", ""),
                        "error": str(e)
                    }
        
        # Run all analyses
        tasks = [analyze_with_limit(page) for page in pages]
        results = await asyncio.gather(*tasks)
        
        return list(results)
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        concurrency: int = 10,
    ) -> List[List[float]]:
        """
        Get embeddings for multiple texts.
        
        Returns:
            List of embedding vectors
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def get_with_limit(text: str) -> List[float]:
            async with semaphore:
                return await self.llm_service.get_embedding(text)
        
        tasks = [get_with_limit(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    # =========================================
    # Helper Methods
    # =========================================
    
    async def _safe_analyze(
        self,
        key: str,
        coro,
    ) -> tuple:
        """Run analysis safely, catching errors"""
        try:
            result = await coro
            return (key, result, None)
        except TaskDisabledError:
            return (key, None, None)  # Not an error, just disabled
        except Exception as e:
            logger.warning(f"Analysis '{key}' failed: {e}")
            return (key, None, e)
    
    def _prepare_site_data(
        self,
        crawl_data: Dict[str, Any],
        page_analyses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare site data for synthesis"""
        # Calculate aggregates
        content_scores = [
            p.get("content_quality", {}).get("overall_score", 0)
            for p in page_analyses
            if p.get("content_quality")
        ]
        
        avg_content_score = (
            sum(content_scores) / len(content_scores)
            if content_scores else None
        )
        
        # Count issues
        issues = {}
        for analysis in page_analyses:
            for error in analysis.get("errors", []):
                issue_type = error.get("type", "unknown")
                issues[issue_type] = issues.get(issue_type, 0) + 1
        
        top_issues = [
            {"type": k, "count": v}
            for k, v in sorted(issues.items(), key=lambda x: -x[1])
        ]
        
        # Get page samples with summaries
        page_samples = [
            {
                "url": p.get("url", ""),
                "summary": p.get("summary", {}).get("summary", "")
            }
            for p in page_analyses
            if p.get("summary")
        ][:10]
        
        return {
            "base_url": crawl_data.get("base_url", ""),
            "total_pages": crawl_data.get("total_pages", len(page_analyses)),
            "total_issues": sum(issues.values()),
            "avg_content_score": avg_content_score,
            "broken_links": crawl_data.get("broken_links", 0),
            "missing_meta": crawl_data.get("missing_meta_count", 0),
            "thin_content_pages": crawl_data.get("thin_content_count", 0),
            "orphan_pages": crawl_data.get("orphan_pages", 0),
            "top_issues": top_issues,
            "page_samples": page_samples,
        }
    
    def _prepare_page_inventory(
        self,
        page_analyses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Prepare page inventory for content strategy"""
        inventory = []
        
        for analysis in page_analyses:
            category = analysis.get("category", {})
            topics = analysis.get("topics", {})
            
            inventory.append({
                "url": analysis.get("url", ""),
                "category": category.get("primary_category") if category else "unknown",
                "primary_topic": topics.get("primary_topic") if topics else None,
                "keywords": topics.get("keywords", []) if topics else [],
            })
        
        return inventory
    
    def _prepare_page_samples(
        self,
        page_analyses: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Prepare page samples for brand voice analysis"""
        samples = []
        
        for analysis in page_analyses:
            if analysis.get("content"):
                samples.append({
                    "url": analysis.get("url", ""),
                    "content": analysis.get("content", "")[:2000]
                })
        
        # Return diverse sample (different categories if possible)
        return samples[:10]
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary"""
        return self.llm_service.get_usage_summary()


# =========================================
# Convenience Functions
# =========================================

async def quick_analyze_page(
    url: str,
    content: str,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Quick single-page analysis without tracking.
    Useful for one-off analyses.
    """
    analyzer = ContentAnalyzer(crawl_id="quick_analysis")
    return await analyzer.analyze_page_basic(url, content, title)


async def quick_analyze_url(
    url: str,
) -> Dict[str, Any]:
    """
    Fetch and analyze a URL.
    Convenience function for quick testing.
    """
    import httpx
    from bs4 import BeautifulSoup
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True, timeout=30)
        html = response.text
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract content
    title = soup.title.string if soup.title else None
    
    # Get meta description
    meta_desc = None
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag:
        meta_desc = meta_tag.get('content')
    
    # Get main content
    for element in soup(['script', 'style', 'nav', 'footer', 'header']):
        element.decompose()
    content = soup.get_text(separator=' ', strip=True)
    
    return await quick_analyze_page(url, content, title)