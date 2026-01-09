"""
Pydantic Models for LLM Structured Outputs

These models define the expected structure of LLM responses.
Using Instructor, the LLM will return data that validates against these schemas.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


# =========================================
# TIER 1: Basic Analysis Models
# =========================================

class PageSummary(BaseModel):
    """Summary of a page's content and purpose"""
    summary: str = Field(
        ..., 
        description="2-3 sentence summary of the page content",
        max_length=500
    )
    page_purpose: str = Field(
        ..., 
        description="Primary purpose of the page (inform, sell, convert, etc.)"
    )
    target_audience: Optional[str] = Field(
        None, 
        description="Inferred target audience for this content"
    )
    key_message: Optional[str] = Field(
        None,
        description="The main message or value proposition"
    )
    content_type: str = Field(
        ...,
        description="Type of content (article, product, landing, form, etc.)"
    )


class PageCategory(str, Enum):
    """Standard page categories"""
    HOMEPAGE = "homepage"
    PRODUCT = "product"
    CATEGORY = "category"
    BLOG_POST = "blog_post"
    LANDING_PAGE = "landing_page"
    ABOUT = "about"
    CONTACT = "contact"
    FAQ = "faq"
    PRICING = "pricing"
    LEGAL = "legal"
    SUPPORT = "support"
    DOCUMENTATION = "documentation"
    PORTFOLIO = "portfolio"
    TESTIMONIALS = "testimonials"
    CAREERS = "careers"
    NEWS = "news"
    EVENT = "event"
    RESOURCE = "resource"
    TOOL = "tool"
    OTHER = "other"


class PageCategorization(BaseModel):
    """Categorization of a page"""
    primary_category: PageCategory = Field(
        ...,
        description="The main category that best describes this page"
    )
    secondary_category: Optional[PageCategory] = Field(
        None,
        description="Secondary category if applicable"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the categorization (0-1)"
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for the categorization"
    )


class TopicExtraction(BaseModel):
    """Extracted topics and keywords from page content"""
    primary_topic: str = Field(
        ...,
        description="The main topic of the page"
    )
    secondary_topics: List[str] = Field(
        default_factory=list,
        description="Secondary topics covered",
        max_length=5
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Relevant keywords for SEO",
        max_length=10
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Named entities mentioned (people, places, products)",
        max_length=10
    )
    industry: Optional[str] = Field(
        None,
        description="Industry or niche this content belongs to"
    )


class TitleQualityAssessment(BaseModel):
    """Assessment of title and meta description quality"""
    title_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall title quality score (0-100)"
    )
    title_issues: List[str] = Field(
        default_factory=list,
        description="Issues with the current title"
    )
    title_suggestion: Optional[str] = Field(
        None,
        description="Suggested improved title"
    )
    meta_description_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Meta description quality score (0-100)"
    )
    meta_description_issues: List[str] = Field(
        default_factory=list,
        description="Issues with the meta description"
    )
    meta_description_suggestion: Optional[str] = Field(
        None,
        description="Suggested improved meta description"
    )


# =========================================
# TIER 2: Detailed Analysis Models
# =========================================

class ContentStrength(BaseModel):
    """A strength in the content"""
    aspect: str = Field(..., description="What aspect is strong")
    explanation: str = Field(..., description="Why this is a strength")


class ContentWeakness(BaseModel):
    """A weakness in the content"""
    aspect: str = Field(..., description="What aspect needs improvement")
    explanation: str = Field(..., description="Why this is a weakness")
    suggestion: str = Field(..., description="How to improve it")
    priority: Literal["high", "medium", "low"] = Field(
        ..., 
        description="Priority level for fixing"
    )


class ContentQualityAnalysis(BaseModel):
    """Comprehensive content quality assessment"""
    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall content quality score (0-100)"
    )
    
    # Sub-scores
    clarity_score: int = Field(..., ge=0, le=100)
    relevance_score: int = Field(..., ge=0, le=100)
    engagement_score: int = Field(..., ge=0, le=100)
    structure_score: int = Field(..., ge=0, le=100)
    
    # Analysis
    strengths: List[ContentStrength] = Field(
        default_factory=list,
        max_length=5
    )
    weaknesses: List[ContentWeakness] = Field(
        default_factory=list,
        max_length=5
    )
    
    # Quick wins
    quick_wins: List[str] = Field(
        default_factory=list,
        description="Easy improvements that can be made quickly",
        max_length=3
    )
    
    # Overall assessment
    summary: str = Field(
        ...,
        description="Brief summary of content quality",
        max_length=300
    )


class SEORecommendation(BaseModel):
    """A single SEO recommendation"""
    issue: str = Field(..., description="The SEO issue identified")
    recommendation: str = Field(..., description="What to do about it")
    impact: Literal["high", "medium", "low"] = Field(
        ...,
        description="Expected impact if fixed"
    )
    effort: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Effort required to implement"
    )
    category: str = Field(
        ...,
        description="Category (technical, content, structure, etc.)"
    )


class SEOAnalysis(BaseModel):
    """SEO recommendations for a page"""
    seo_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall SEO health score"
    )
    recommendations: List[SEORecommendation] = Field(
        default_factory=list,
        max_length=10
    )
    target_keywords: List[str] = Field(
        default_factory=list,
        description="Suggested target keywords",
        max_length=5
    )
    keyword_opportunities: List[str] = Field(
        default_factory=list,
        description="Keywords the page could rank for with improvements",
        max_length=5
    )


class AltTextSuggestion(BaseModel):
    """Suggested alt text for an image"""
    image_context: str = Field(
        ...,
        description="Understanding of what the image likely shows based on context"
    )
    suggested_alt_text: str = Field(
        ...,
        description="Suggested alt text (max 125 chars)",
        max_length=125
    )
    is_decorative: bool = Field(
        default=False,
        description="Whether the image appears to be decorative"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the suggestion"
    )


class MetaDescriptionSuggestion(BaseModel):
    """Generated meta description"""
    meta_description: str = Field(
        ...,
        description="Optimized meta description (150-160 chars)",
        min_length=120,
        max_length=160
    )
    includes_cta: bool = Field(
        default=False,
        description="Whether it includes a call-to-action"
    )
    target_keyword: Optional[str] = Field(
        None,
        description="Primary keyword targeted"
    )


class ReadabilityAnalysis(BaseModel):
    """Readability assessment"""
    readability_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall readability score (higher = easier to read)"
    )
    grade_level: str = Field(
        ...,
        description="Approximate reading grade level"
    )
    average_sentence_length: str = Field(
        ...,
        description="Assessment of sentence length (short/medium/long)"
    )
    vocabulary_complexity: str = Field(
        ...,
        description="Vocabulary complexity (simple/moderate/complex)"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Specific readability issues"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )


# =========================================
# TIER 3: Synthesis and Report Models
# =========================================

class CriticalIssue(BaseModel):
    """A critical issue that needs immediate attention"""
    title: str
    description: str
    pages_affected: int
    recommended_action: str
    priority: Literal["critical", "high", "medium"]


class StrategicRecommendation(BaseModel):
    """A strategic recommendation for the site"""
    title: str
    description: str
    expected_impact: str
    effort_estimate: str
    timeline: str


class ExecutiveSummary(BaseModel):
    """Executive-level site analysis summary"""
    # Overview
    site_health_score: int = Field(..., ge=0, le=100)
    one_line_summary: str = Field(
        ...,
        description="One sentence summary of site health",
        max_length=200
    )
    
    # Scores breakdown
    technical_seo_score: int = Field(..., ge=0, le=100)
    content_quality_score: int = Field(..., ge=0, le=100)
    user_experience_score: int = Field(..., ge=0, le=100)
    trust_signals_score: int = Field(..., ge=0, le=100)
    
    # Critical issues
    critical_issues: List[CriticalIssue] = Field(
        default_factory=list,
        max_length=5
    )
    
    # Recommendations
    quick_wins: List[str] = Field(
        default_factory=list,
        description="Easy fixes for immediate impact",
        max_length=5
    )
    strategic_recommendations: List[StrategicRecommendation] = Field(
        default_factory=list,
        max_length=5
    )
    
    # Summary paragraphs
    strengths_summary: str = Field(
        ...,
        description="Summary of what the site does well"
    )
    weaknesses_summary: str = Field(
        ...,
        description="Summary of areas needing improvement"
    )
    action_plan_summary: str = Field(
        ...,
        description="Recommended action plan overview"
    )


class BrandVoiceAttribute(BaseModel):
    """An attribute of brand voice"""
    attribute: str = Field(..., description="e.g., 'professional', 'casual', 'friendly'")
    score: int = Field(..., ge=0, le=100, description="How strongly present (0-100)")
    evidence: str = Field(..., description="Example from content")


class BrandVoiceAnalysis(BaseModel):
    """Brand voice consistency analysis"""
    overall_consistency_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="How consistent is the brand voice across pages"
    )
    
    # Voice attributes detected
    voice_attributes: List[BrandVoiceAttribute] = Field(
        default_factory=list,
        max_length=6
    )
    
    # Primary voice
    primary_tone: str = Field(
        ...,
        description="The dominant tone (e.g., 'professional', 'conversational')"
    )
    formality_level: str = Field(
        ...,
        description="Formality level (formal/semi-formal/casual)"
    )
    
    # Inconsistencies
    inconsistent_pages: List[str] = Field(
        default_factory=list,
        description="Pages that don't match the primary voice",
        max_length=10
    )
    inconsistency_examples: List[str] = Field(
        default_factory=list,
        description="Examples of voice inconsistency",
        max_length=5
    )
    
    # Recommendations
    voice_guidelines: List[str] = Field(
        default_factory=list,
        description="Recommended voice guidelines based on analysis",
        max_length=5
    )


class ContentGap(BaseModel):
    """A gap in content coverage"""
    gap_type: str = Field(..., description="Type of gap (missing page, thin content, etc.)")
    description: str
    priority: Literal["high", "medium", "low"]
    suggested_content: str = Field(..., description="What content to create")
    estimated_impact: str


class ContentStrategyAnalysis(BaseModel):
    """Content strategy recommendations"""
    # Current state
    content_maturity_score: int = Field(..., ge=0, le=100)
    content_coverage_assessment: str = Field(
        ...,
        description="Assessment of how well content covers the topic space"
    )
    
    # Gaps
    content_gaps: List[ContentGap] = Field(
        default_factory=list,
        max_length=10
    )
    
    # Opportunities
    content_opportunities: List[str] = Field(
        default_factory=list,
        description="Opportunities for new content",
        max_length=10
    )
    
    # Strategy recommendations
    pillar_content_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested pillar/cornerstone content",
        max_length=5
    )
    content_cluster_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggested topic clusters to develop",
        max_length=5
    )
    
    # Action plan
    priority_actions: List[str] = Field(
        default_factory=list,
        description="Prioritized content actions",
        max_length=5
    )


# =========================================
# Usage Tracking Models
# =========================================

class LLMUsageRecord(BaseModel):
    """Record of LLM API usage for cost tracking"""
    crawl_id: str
    task_type: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    success: bool
    error_message: Optional[str] = None
    duration_ms: int