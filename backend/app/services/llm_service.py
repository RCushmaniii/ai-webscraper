"""
LLM Service - Core Abstraction Layer

This service provides:
- Unified interface for LLM tasks
- Structured outputs with Pydantic validation (via Instructor)
- Cost tracking and budget management
- Retry logic with exponential backoff
- Rate limiting

Usage:
    from app.services.llm_service import LLMService, LLMTask
    
    service = LLMService()
    result = await service.analyze_page_summary(page_content)
"""

import asyncio
import logging
import time
from typing import TypeVar, Type, Optional, Dict, Any, List, Union
from datetime import datetime, timezone
import tiktoken

# OpenAI SDK
from openai import AsyncOpenAI, OpenAI
import instructor

# Internal imports
from app.core.llm_config import (
    LLMTask,
    TaskConfig,
    LLMSettings,
    get_llm_settings,
    get_task_config,
    is_task_enabled,
    estimate_cost,
)
from app.models.llm_models import (
    PageSummary,
    PageCategorization,
    TopicExtraction,
    TitleQualityAssessment,
    ContentQualityAnalysis,
    SEOAnalysis,
    AltTextSuggestion,
    MetaDescriptionSuggestion,
    ReadabilityAnalysis,
    ExecutiveSummary,
    BrandVoiceAnalysis,
    ContentStrategyAnalysis,
    LLMUsageRecord,
)

logger = logging.getLogger(__name__)

# Generic type for Pydantic models
T = TypeVar('T')


class LLMServiceError(Exception):
    """Base exception for LLM service errors"""
    pass


class TaskDisabledError(LLMServiceError):
    """Raised when a task is disabled by feature flags"""
    pass


class BudgetExceededError(LLMServiceError):
    """Raised when cost budget is exceeded"""
    pass


class RateLimitError(LLMServiceError):
    """Raised when rate limit is hit"""
    pass


class CostTracker:
    """Tracks LLM costs for a crawl session"""
    
    def __init__(self, crawl_id: str, max_cost: float = 5.0):
        self.crawl_id = crawl_id
        self.max_cost = max_cost
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        self.records: List[LLMUsageRecord] = []
    
    def add_usage(
        self,
        task_type: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        success: bool,
        error_message: Optional[str] = None,
        duration_ms: int = 0
    ) -> None:
        """Record usage and check budget"""
        self.total_cost += cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.request_count += 1
        
        record = LLMUsageRecord(
            crawl_id=self.crawl_id,
            task_type=task_type,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        self.records.append(record)
        
        logger.info(
            f"LLM Usage: {task_type} | {model} | "
            f"Tokens: {input_tokens}+{output_tokens} | "
            f"Cost: ${cost:.6f} | Total: ${self.total_cost:.4f}"
        )
    
    def check_budget(self) -> None:
        """Raise error if budget exceeded"""
        if self.total_cost >= self.max_cost:
            raise BudgetExceededError(
                f"Cost budget exceeded: ${self.total_cost:.4f} >= ${self.max_cost:.2f}"
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary"""
        return {
            "crawl_id": self.crawl_id,
            "total_cost_usd": round(self.total_cost, 6),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "request_count": self.request_count,
            "budget_remaining_usd": round(self.max_cost - self.total_cost, 6),
        }


class LLMService:
    """
    Main LLM service for content analysis.
    
    Uses OpenAI API with Instructor for structured outputs.
    Supports async operations and includes cost tracking.
    """
    
    def __init__(
        self,
        crawl_id: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ):
        self.settings = settings or get_llm_settings()
        self.crawl_id = crawl_id or "unknown"
        
        # Initialize OpenAI clients
        self._init_clients()
        
        # Cost tracking
        self.cost_tracker = CostTracker(
            crawl_id=self.crawl_id,
            max_cost=self.settings.max_cost_per_crawl
        )
        
        # Token counter
        self._encoding = None
    
    def _init_clients(self) -> None:
        """Initialize OpenAI clients with Instructor"""
        if not self.settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
            self._async_client = None
            self._sync_client = None
            return
        
        # Async client with Instructor
        base_async_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self._async_client = instructor.from_openai(base_async_client)
        
        # Sync client with Instructor (for non-async contexts)
        base_sync_client = OpenAI(api_key=self.settings.openai_api_key)
        self._sync_client = instructor.from_openai(base_sync_client)
        
        # Raw clients for embeddings (Instructor doesn't support embeddings)
        self._raw_async_client = base_async_client
        self._raw_sync_client = base_sync_client
    
    def _get_encoding(self):
        """Get tokenizer for counting tokens"""
        if self._encoding is None:
            try:
                self._encoding = tiktoken.encoding_for_model("gpt-4o")
            except Exception:
                self._encoding = tiktoken.get_encoding("cl100k_base")
        return self._encoding
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not text:
            return 0
        encoding = self._get_encoding()
        return len(encoding.encode(text))
    
    async def _complete_structured(
        self,
        task: LLMTask,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        """
        Make a structured completion request.
        
        Uses Instructor to get validated Pydantic model responses.
        """
        # Check if task is enabled
        if not is_task_enabled(task, self.settings):
            raise TaskDisabledError(f"Task {task.value} is disabled by feature flags")
        
        # Check budget
        self.cost_tracker.check_budget()
        
        # Get task config
        config = get_task_config(task)
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Count input tokens
        full_prompt = (system_prompt or "") + prompt
        input_tokens = self.count_tokens(full_prompt)
        
        # Make request with retry
        start_time = time.time()
        output_tokens = 0
        success = False
        error_message = None
        
        for attempt in range(self.settings.max_retries):
            try:
                response = await self._async_client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    response_model=response_model,
                    timeout=config.timeout_seconds,
                )
                
                success = True
                # Estimate output tokens from response
                output_tokens = self.count_tokens(response.model_dump_json())
                
                break
                
            except Exception as e:
                error_message = str(e)
                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{self.settings.max_retries}): {e}"
                )
                
                if attempt < self.settings.max_retries - 1:
                    delay = self.settings.retry_delay_seconds * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise LLMServiceError(f"LLM request failed after {self.settings.max_retries} attempts: {e}")
        
        # Calculate cost and track
        duration_ms = int((time.time() - start_time) * 1000)
        cost = estimate_cost(task, input_tokens, output_tokens)
        
        self.cost_tracker.add_usage(
            task_type=task.value,
            model=config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        return response
    
    async def _complete_raw(
        self,
        task: LLMTask,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Make a raw (non-structured) completion request"""
        # Check if task is enabled
        if not is_task_enabled(task, self.settings):
            raise TaskDisabledError(f"Task {task.value} is disabled by feature flags")
        
        # Check budget
        self.cost_tracker.check_budget()
        
        config = get_task_config(task)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        input_tokens = self.count_tokens((system_prompt or "") + prompt)
        start_time = time.time()
        
        response = await self._raw_async_client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout_seconds,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        output_text = response.choices[0].message.content or ""
        output_tokens = response.usage.completion_tokens if response.usage else self.count_tokens(output_text)
        
        cost = estimate_cost(task, input_tokens, output_tokens)
        
        self.cost_tracker.add_usage(
            task_type=task.value,
            model=config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            success=True,
            duration_ms=duration_ms
        )
        
        return output_text
    
    async def get_embedding(self, text: str, dimensions: int = 512) -> List[float]:
        """Get embedding vector for text"""
        if not is_task_enabled(LLMTask.SEMANTIC_EMBEDDING, self.settings):
            raise TaskDisabledError("Embeddings are disabled")
        
        self.cost_tracker.check_budget()
        
        config = get_task_config(LLMTask.SEMANTIC_EMBEDDING)
        input_tokens = self.count_tokens(text)
        
        start_time = time.time()
        
        response = await self._raw_async_client.embeddings.create(
            model=config.model,
            input=text,
            dimensions=dimensions
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        embedding = response.data[0].embedding
        
        cost = (input_tokens / 1000) * config.cost_per_1k_input
        
        self.cost_tracker.add_usage(
            task_type=LLMTask.SEMANTIC_EMBEDDING.value,
            model=config.model,
            input_tokens=input_tokens,
            output_tokens=0,
            cost=cost,
            success=True,
            duration_ms=duration_ms
        )
        
        return embedding
    
    # =========================================
    # TIER 1: Basic Analysis Methods
    # =========================================
    
    async def analyze_page_summary(
        self,
        content: str,
        url: str,
        title: Optional[str] = None,
    ) -> PageSummary:
        """Generate a summary of page content"""
        
        # Truncate content if too long
        max_content_tokens = 3000
        if self.count_tokens(content) > max_content_tokens:
            encoding = self._get_encoding()
            tokens = encoding.encode(content)[:max_content_tokens]
            content = encoding.decode(tokens)
        
        prompt = f"""Analyze this web page and provide a summary.

URL: {url}
Title: {title or 'Not provided'}

Page Content:
{content}

Provide a concise summary of what this page is about, its purpose, target audience, and key message."""
        
        return await self._complete_structured(
            task=LLMTask.PAGE_SUMMARY,
            prompt=prompt,
            response_model=PageSummary,
            system_prompt="You are a web content analyst. Provide concise, accurate summaries."
        )
    
    async def categorize_page(
        self,
        content: str,
        url: str,
        title: Optional[str] = None,
    ) -> PageCategorization:
        """Categorize a page by type"""
        
        # Use less content for categorization
        content_preview = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""Categorize this web page.

URL: {url}
Title: {title or 'Not provided'}

Content Preview:
{content_preview}

Determine the primary category that best describes this page's purpose."""
        
        return await self._complete_structured(
            task=LLMTask.PAGE_CATEGORIZATION,
            prompt=prompt,
            response_model=PageCategorization,
            system_prompt="You are a web page classifier. Categorize pages accurately based on their content and purpose."
        )
    
    async def extract_topics(
        self,
        content: str,
        url: str,
        title: Optional[str] = None,
    ) -> TopicExtraction:
        """Extract topics and keywords from page"""
        
        content_preview = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""Extract the main topics and keywords from this page.

URL: {url}
Title: {title or 'Not provided'}

Content:
{content_preview}

Identify the primary topic, secondary topics, relevant SEO keywords, and any named entities."""
        
        return await self._complete_structured(
            task=LLMTask.TOPIC_EXTRACTION,
            prompt=prompt,
            response_model=TopicExtraction,
            system_prompt="You are an SEO specialist and content analyst. Extract relevant topics and keywords."
        )
    
    async def assess_title_quality(
        self,
        title: str,
        meta_description: Optional[str],
        content_preview: str,
        url: str,
    ) -> TitleQualityAssessment:
        """Assess quality of title and meta description"""
        
        prompt = f"""Assess the quality of this page's title and meta description.

URL: {url}
Title: {title}
Meta Description: {meta_description or 'Not provided'}

Content Preview:
{content_preview[:1500]}

Evaluate both for SEO effectiveness, clarity, and accuracy. Suggest improvements if needed."""
        
        return await self._complete_structured(
            task=LLMTask.TITLE_QUALITY,
            prompt=prompt,
            response_model=TitleQualityAssessment,
            system_prompt="You are an SEO expert. Evaluate titles and meta descriptions for search optimization."
        )
    
    # =========================================
    # TIER 2: Detailed Analysis Methods
    # =========================================
    
    async def analyze_content_quality(
        self,
        content: str,
        url: str,
        title: Optional[str] = None,
        page_type: Optional[str] = None,
    ) -> ContentQualityAnalysis:
        """Comprehensive content quality analysis"""
        
        # Truncate for reasonable token usage
        max_tokens = 4000
        if self.count_tokens(content) > max_tokens:
            encoding = self._get_encoding()
            tokens = encoding.encode(content)[:max_tokens]
            content = encoding.decode(tokens)
        
        prompt = f"""Perform a comprehensive content quality analysis.

URL: {url}
Title: {title or 'Not provided'}
Page Type: {page_type or 'Unknown'}

Content:
{content}

Analyze:
1. Overall quality and effectiveness
2. Clarity and readability
3. Relevance to apparent purpose
4. Engagement potential
5. Content structure

Identify strengths, weaknesses, and quick wins for improvement."""
        
        return await self._complete_structured(
            task=LLMTask.CONTENT_QUALITY,
            prompt=prompt,
            response_model=ContentQualityAnalysis,
            system_prompt="You are a professional content strategist. Provide actionable content quality assessments."
        )
    
    async def generate_seo_recommendations(
        self,
        content: str,
        url: str,
        title: Optional[str] = None,
        meta_description: Optional[str] = None,
        h1: Optional[str] = None,
        word_count: int = 0,
    ) -> SEOAnalysis:
        """Generate SEO recommendations for a page"""
        
        content_preview = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""Provide SEO recommendations for this page.

URL: {url}
Title: {title or 'Not provided'}
Meta Description: {meta_description or 'Not provided'}
H1: {h1 or 'Not provided'}
Word Count: {word_count}

Content Preview:
{content_preview}

Analyze SEO health and provide specific, actionable recommendations. Consider:
- Title and meta optimization
- Content structure and keywords
- Technical SEO signals
- User experience factors"""
        
        return await self._complete_structured(
            task=LLMTask.SEO_RECOMMENDATIONS,
            prompt=prompt,
            response_model=SEOAnalysis,
            system_prompt="You are an SEO expert. Provide specific, actionable recommendations with clear impact assessments."
        )
    
    async def suggest_alt_text(
        self,
        surrounding_text: str,
        image_filename: str,
        page_context: str,
    ) -> AltTextSuggestion:
        """Suggest alt text for an image based on context"""
        
        prompt = f"""Suggest appropriate alt text for an image.

Image Filename: {image_filename}
Surrounding Text: {surrounding_text[:500]}
Page Context: {page_context[:500]}

Based on the context, suggest descriptive alt text that:
- Describes what the image likely shows
- Is concise (max 125 characters)
- Is useful for screen readers
- Considers if the image might be decorative"""
        
        return await self._complete_structured(
            task=LLMTask.ALT_TEXT_SUGGESTION,
            prompt=prompt,
            response_model=AltTextSuggestion,
            system_prompt="You are an accessibility expert. Suggest helpful, descriptive alt text for images."
        )
    
    async def generate_meta_description(
        self,
        content: str,
        title: str,
        url: str,
    ) -> MetaDescriptionSuggestion:
        """Generate an optimized meta description"""
        
        content_preview = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""Generate an optimized meta description for this page.

URL: {url}
Title: {title}

Content:
{content_preview}

Create a compelling meta description that:
- Is 150-160 characters
- Includes the main topic/keyword naturally
- Has a subtle call-to-action
- Accurately represents the page content
- Encourages clicks from search results"""
        
        return await self._complete_structured(
            task=LLMTask.META_DESCRIPTION_GENERATOR,
            prompt=prompt,
            response_model=MetaDescriptionSuggestion,
            system_prompt="You are an SEO copywriter. Write compelling meta descriptions that drive clicks."
        )
    
    # =========================================
    # TIER 3: Synthesis Methods
    # =========================================
    
    async def generate_executive_summary(
        self,
        site_data: Dict[str, Any],
    ) -> ExecutiveSummary:
        """Generate executive-level site analysis summary"""
        
        prompt = f"""Generate an executive summary for this website analysis.

Site: {site_data.get('base_url', 'Unknown')}
Pages Crawled: {site_data.get('total_pages', 0)}
Issues Found: {site_data.get('total_issues', 0)}

Key Metrics:
- Average Content Quality: {site_data.get('avg_content_score', 'N/A')}
- Broken Links: {site_data.get('broken_links', 0)}
- Missing Meta Descriptions: {site_data.get('missing_meta', 0)}
- Thin Content Pages: {site_data.get('thin_content_pages', 0)}
- Orphan Pages: {site_data.get('orphan_pages', 0)}

Top Issues by Frequency:
{self._format_top_issues(site_data.get('top_issues', []))}

Sample Page Summaries:
{self._format_page_samples(site_data.get('page_samples', []))}

Create a comprehensive executive summary with:
1. Overall site health score and one-line summary
2. Breakdown of technical, content, UX, and trust scores
3. Critical issues requiring immediate attention
4. Quick wins for immediate impact
5. Strategic recommendations for long-term improvement"""
        
        return await self._complete_structured(
            task=LLMTask.EXECUTIVE_SUMMARY,
            prompt=prompt,
            response_model=ExecutiveSummary,
            system_prompt="You are a senior digital strategist. Create executive-level reports that drive action."
        )
    
    async def analyze_brand_voice(
        self,
        page_samples: List[Dict[str, str]],
        site_url: str,
    ) -> BrandVoiceAnalysis:
        """Analyze brand voice consistency across pages"""
        
        samples_text = "\n\n---\n\n".join([
            f"Page: {p.get('url', 'Unknown')}\nContent:\n{p.get('content', '')[:1000]}"
            for p in page_samples[:10]
        ])
        
        prompt = f"""Analyze the brand voice consistency across this website.

Site: {site_url}

Content Samples from Different Pages:
{samples_text}

Analyze:
1. Overall voice consistency across pages
2. Key voice attributes (tone, formality, personality)
3. Any inconsistencies between pages
4. Recommendations for brand voice guidelines"""
        
        return await self._complete_structured(
            task=LLMTask.BRAND_VOICE_ANALYSIS,
            prompt=prompt,
            response_model=BrandVoiceAnalysis,
            system_prompt="You are a brand strategist. Analyze brand voice for consistency and provide actionable guidelines."
        )
    
    async def generate_content_strategy(
        self,
        site_data: Dict[str, Any],
        page_inventory: List[Dict[str, Any]],
    ) -> ContentStrategyAnalysis:
        """Generate content strategy recommendations"""
        
        # Summarize page inventory
        page_summary = self._summarize_page_inventory(page_inventory)
        
        prompt = f"""Generate content strategy recommendations for this website.

Site: {site_data.get('base_url', 'Unknown')}
Total Pages: {len(page_inventory)}

Page Inventory Summary:
{page_summary}

Current Content Coverage:
- Blog posts: {site_data.get('blog_count', 0)}
- Product pages: {site_data.get('product_count', 0)}
- Landing pages: {site_data.get('landing_count', 0)}
- Support/FAQ pages: {site_data.get('support_count', 0)}

Analyze:
1. Current content maturity and coverage
2. Content gaps and missing opportunities
3. Pillar content recommendations
4. Topic cluster suggestions
5. Priority actions for content improvement"""
        
        return await self._complete_structured(
            task=LLMTask.CONTENT_STRATEGY,
            prompt=prompt,
            response_model=ContentStrategyAnalysis,
            system_prompt="You are a content strategist. Provide data-driven content strategy recommendations."
        )
    
    # =========================================
    # Helper Methods
    # =========================================
    
    def _format_top_issues(self, issues: List[Dict]) -> str:
        """Format top issues for prompt"""
        if not issues:
            return "No issues data available"
        
        lines = []
        for issue in issues[:10]:
            lines.append(f"- {issue.get('type', 'Unknown')}: {issue.get('count', 0)} occurrences")
        return "\n".join(lines)
    
    def _format_page_samples(self, samples: List[Dict]) -> str:
        """Format page samples for prompt"""
        if not samples:
            return "No page samples available"
        
        lines = []
        for sample in samples[:5]:
            lines.append(
                f"- {sample.get('url', 'Unknown')}: {sample.get('summary', 'No summary')[:200]}"
            )
        return "\n".join(lines)
    
    def _summarize_page_inventory(self, pages: List[Dict]) -> str:
        """Summarize page inventory for prompt"""
        if not pages:
            return "No pages available"
        
        # Group by category
        categories = {}
        for page in pages:
            cat = page.get('category', 'other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(page.get('url', ''))
        
        lines = []
        for cat, urls in categories.items():
            lines.append(f"- {cat}: {len(urls)} pages")
            for url in urls[:3]:
                lines.append(f"  - {url}")
            if len(urls) > 3:
                lines.append(f"  - ... and {len(urls) - 3} more")
        
        return "\n".join(lines)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary for this session"""
        return self.cost_tracker.get_summary()
    
    def get_usage_records(self) -> List[LLMUsageRecord]:
        """Get all usage records"""
        return self.cost_tracker.records