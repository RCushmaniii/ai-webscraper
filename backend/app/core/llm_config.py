"""
LLM Configuration and Task Definitions

This module defines:
- Available LLM tasks and their configurations
- Model selection per task type
- Cost tracking parameters
- Rate limiting settings
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel
from functools import lru_cache


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"  # Future support


class LLMTask(str, Enum):
    """
    Available LLM tasks categorized by tier:
    
    Tier 1 (Cheap, Fast) - Run per page during crawl
    Tier 2 (Medium) - Run per page on-demand or batch
    Tier 3 (Expensive) - Run once per crawl for synthesis
    """
    # Tier 1: Basic analysis (gpt-4o-mini)
    PAGE_SUMMARY = "page_summary"
    PAGE_CATEGORIZATION = "page_categorization"
    TOPIC_EXTRACTION = "topic_extraction"
    TITLE_QUALITY = "title_quality"
    
    # Tier 2: Detailed analysis (gpt-4o-mini or gpt-4o)
    CONTENT_QUALITY = "content_quality"
    SEO_RECOMMENDATIONS = "seo_recommendations"
    ALT_TEXT_SUGGESTION = "alt_text_suggestion"
    META_DESCRIPTION_GENERATOR = "meta_description_generator"
    READABILITY_ANALYSIS = "readability_analysis"
    
    # Tier 3: Synthesis and reports (gpt-4o)
    EXECUTIVE_SUMMARY = "executive_summary"
    BRAND_VOICE_ANALYSIS = "brand_voice_analysis"
    CONTENT_STRATEGY = "content_strategy"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    
    # Embeddings (text-embedding-3-small)
    SEMANTIC_EMBEDDING = "semantic_embedding"


class TaskConfig(BaseModel):
    """Configuration for a specific LLM task"""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str
    max_tokens: int
    temperature: float
    tier: int  # 1, 2, or 3
    description: str
    
    # Cost per 1K tokens (for tracking)
    cost_per_1k_input: float
    cost_per_1k_output: float
    
    # Optional settings
    response_format: Optional[str] = None  # "json_object" for structured output
    timeout_seconds: int = 30


# Model pricing (as of Dec 2024)
OPENAI_PRICING = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}


# Task configurations
TASK_CONFIGS: Dict[LLMTask, TaskConfig] = {
    # =========================================
    # TIER 1: Cheap, fast, run during crawl
    # =========================================
    LLMTask.PAGE_SUMMARY: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=300,
        temperature=0.3,
        tier=1,
        description="Generate a concise summary of page content",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
    ),
    
    LLMTask.PAGE_CATEGORIZATION: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=100,
        temperature=0.1,
        tier=1,
        description="Categorize page type (blog, product, landing, etc.)",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
    ),
    
    LLMTask.TOPIC_EXTRACTION: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=150,
        temperature=0.2,
        tier=1,
        description="Extract main topics and keywords from page",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
    ),
    
    LLMTask.TITLE_QUALITY: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=200,
        temperature=0.2,
        tier=1,
        description="Assess title and meta description quality",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
    ),
    
    # =========================================
    # TIER 2: Medium cost, detailed analysis
    # =========================================
    LLMTask.CONTENT_QUALITY: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=500,
        temperature=0.4,
        tier=2,
        description="Comprehensive content quality assessment",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
        timeout_seconds=45,
    ),
    
    LLMTask.SEO_RECOMMENDATIONS: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=400,
        temperature=0.4,
        tier=2,
        description="Generate SEO improvement recommendations",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
        timeout_seconds=45,
    ),
    
    LLMTask.ALT_TEXT_SUGGESTION: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=100,
        temperature=0.3,
        tier=2,
        description="Suggest alt text for images based on context",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
    ),
    
    LLMTask.META_DESCRIPTION_GENERATOR: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=200,
        temperature=0.5,
        tier=2,
        description="Generate optimized meta descriptions",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
    ),
    
    LLMTask.READABILITY_ANALYSIS: TaskConfig(
        model="gpt-4o-mini",
        max_tokens=300,
        temperature=0.3,
        tier=2,
        description="Analyze content readability and clarity",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o-mini"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o-mini"]["output"],
        response_format="json_object",
    ),
    
    # =========================================
    # TIER 3: Expensive, synthesis tasks
    # =========================================
    LLMTask.EXECUTIVE_SUMMARY: TaskConfig(
        model="gpt-4o",
        max_tokens=2000,
        temperature=0.5,
        tier=3,
        description="Generate executive-level site analysis report",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o"]["output"],
        response_format="json_object",
        timeout_seconds=90,
    ),
    
    LLMTask.BRAND_VOICE_ANALYSIS: TaskConfig(
        model="gpt-4o",
        max_tokens=1500,
        temperature=0.4,
        tier=3,
        description="Analyze brand voice consistency across pages",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o"]["output"],
        response_format="json_object",
        timeout_seconds=90,
    ),
    
    LLMTask.CONTENT_STRATEGY: TaskConfig(
        model="gpt-4o",
        max_tokens=2000,
        temperature=0.5,
        tier=3,
        description="Generate content strategy recommendations",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o"]["output"],
        response_format="json_object",
        timeout_seconds=90,
    ),
    
    LLMTask.COMPETITIVE_ANALYSIS: TaskConfig(
        model="gpt-4o",
        max_tokens=1500,
        temperature=0.4,
        tier=3,
        description="Analyze competitive positioning based on content",
        cost_per_1k_input=OPENAI_PRICING["gpt-4o"]["input"],
        cost_per_1k_output=OPENAI_PRICING["gpt-4o"]["output"],
        response_format="json_object",
        timeout_seconds=90,
    ),
    
    # =========================================
    # EMBEDDINGS
    # =========================================
    LLMTask.SEMANTIC_EMBEDDING: TaskConfig(
        model="text-embedding-3-small",
        max_tokens=0,  # Not applicable for embeddings
        temperature=0.0,
        tier=1,
        description="Generate embeddings for semantic similarity",
        cost_per_1k_input=OPENAI_PRICING["text-embedding-3-small"]["input"],
        cost_per_1k_output=0.0,
    ),
}


class LLMSettings(BaseModel):
    """Global LLM settings loaded from environment"""
    openai_api_key: str
    default_provider: LLMProvider = LLMProvider.OPENAI
    
    # Feature flags
    enable_llm_basic: bool = True      # Tier 1 tasks
    enable_llm_analysis: bool = True   # Tier 2 tasks
    enable_llm_reports: bool = True    # Tier 3 tasks
    enable_embeddings: bool = True
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_tokens_per_minute: int = 150000
    
    # Cost controls
    max_cost_per_crawl: float = 5.0  # USD
    warn_cost_threshold: float = 1.0  # USD
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


@lru_cache()
def get_llm_settings() -> LLMSettings:
    """Get LLM settings from environment (cached)"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    return LLMSettings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        enable_llm_basic=os.getenv("ENABLE_LLM_BASIC", "true").lower() == "true",
        enable_llm_analysis=os.getenv("ENABLE_LLM_ANALYSIS", "true").lower() == "true",
        enable_llm_reports=os.getenv("ENABLE_LLM_REPORTS", "true").lower() == "true",
        enable_embeddings=os.getenv("ENABLE_EMBEDDINGS", "true").lower() == "true",
        max_cost_per_crawl=float(os.getenv("MAX_LLM_COST_PER_CRAWL", "5.0")),
    )


def get_task_config(task: LLMTask) -> TaskConfig:
    """Get configuration for a specific task"""
    return TASK_CONFIGS[task]


def is_task_enabled(task: LLMTask, settings: LLMSettings = None) -> bool:
    """Check if a task is enabled based on feature flags"""
    if settings is None:
        settings = get_llm_settings()
    
    config = get_task_config(task)
    
    if config.tier == 1:
        return settings.enable_llm_basic
    elif config.tier == 2:
        return settings.enable_llm_analysis
    elif config.tier == 3:
        return settings.enable_llm_reports
    
    # Embeddings
    if task == LLMTask.SEMANTIC_EMBEDDING:
        return settings.enable_embeddings
    
    return False


def estimate_cost(
    task: LLMTask,
    input_tokens: int,
    output_tokens: int = None
) -> float:
    """Estimate cost for a task"""
    config = get_task_config(task)
    
    if output_tokens is None:
        output_tokens = config.max_tokens
    
    input_cost = (input_tokens / 1000) * config.cost_per_1k_input
    output_cost = (output_tokens / 1000) * config.cost_per_1k_output
    
    return input_cost + output_cost