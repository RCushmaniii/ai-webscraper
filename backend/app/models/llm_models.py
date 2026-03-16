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
    """A critical issue — must describe a PATTERN, not just a category"""
    title: str = Field(..., description="A pattern insight, e.g. '5 meta descriptions all overshoot by 7-11 chars — likely a template issue'. NOT a category like 'Meta description issues'.")
    description: str = Field(..., description="The consultant narrative: what's the pattern, why does it matter for the business, and what's the root cause? Cite specific URLs and numbers.")
    pages_affected: int
    recommended_action: str = Field(..., description="The specific fix: 'Trim /services meta from 166 to 155 chars, /about from 165 to 150. Consider a global max-length rule in your CMS.' NOT 'optimize meta descriptions'.")
    priority: Literal["critical", "high", "medium"]
    affected_urls: List[str] = Field(default_factory=list, description="Specific URLs affected by this issue")


class StrategicRecommendation(BaseModel):
    """A strategic recommendation — must connect multiple findings into a bigger picture"""
    title: str = Field(..., description="A strategic insight, e.g. 'Your conversion page (/consultation) has the weakest SEO on the site'. NOT 'Improve SEO'.")
    description: str = Field(..., description="Connect dots: which findings combine to create a bigger problem or opportunity? Reference URLs and numbers. What would a $500/hr consultant say that isn't obvious from the data alone?")
    expected_impact: str = Field(..., description="Specific impact, e.g. 'Reclaiming SERP snippet control on 5 pages could improve CTR by 15-30%'. NOT 'improved visibility'.")
    effort_estimate: str = Field(..., description="e.g. '30 minutes to update all 5 meta descriptions', '2 hours for title rewrite + testing'")
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
        description="Copy-paste fixes. For titles: suggest 5-8 words in format 'Keyword — Modifier | Brand'. For meta descriptions: suggest exactly TWO complete sentences (value prop + CTA). NEVER suggest a one-sentence or one-fragment meta description. Example: 'On /services, replace meta with: \"AI support assistants and document automation tailored for small businesses. See how CushLabs can cut costs and save time.\"'",
        max_length=5
    )
    strategic_recommendations: List[StrategicRecommendation] = Field(
        default_factory=list,
        max_length=5
    )
    
    # Summary paragraphs
    strengths_summary: str = Field(
        ...,
        description="2-3 sentences citing specific data: '100% H1 coverage, all 10 pages load under 1s, zero broken links — the technical foundation is solid.' NOT 'the site has a strong foundation'."
    )
    weaknesses_summary: str = Field(
        ...,
        description="2-3 sentences connecting weaknesses to business impact: 'Only 30% of meta descriptions pass — search engines are writing 7 of 10 snippets for you, which means you have no control over how 70% of your pages appear in search results.' NOT 'meta descriptions need improvement'."
    )
    action_plan_summary: str = Field(
        ...,
        description="Prioritized next steps with time estimates: 'Week 1: Fix the 5 meta descriptions that are 7-11 chars over limit (30 min). Week 2: Rewrite 3 too-short titles targeting primary keywords (1 hr). Month 1: Audit /consultation page copy for conversion optimization.' NOT 'focus on improving SEO'."
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

# =========================================
# Semantic Strategy & CRO Models
# =========================================

class IntentGapAnalysis(BaseModel):
    """Analysis of whether page messaging aligns with the page's purpose"""
    alignment_score: int = Field(..., ge=0, le=100, description="How well the messaging matches the page's inferred purpose (0-100)")
    assessment: str = Field(..., description="1-2 sentence assessment of intent alignment", max_length=300)
    gaps: List[str] = Field(default_factory=list, description="Specific gaps between page purpose and actual messaging", max_length=5)
    suggestions: List[str] = Field(default_factory=list, description="Actionable suggestions to close intent gaps", max_length=3)


class TonePersonaAudit(BaseModel):
    """Analysis of whether the page's tone matches its audience and purpose"""
    tone_match_score: int = Field(..., ge=0, le=100, description="How well the tone fits the page purpose and audience (0-100)")
    detected_tone: str = Field(..., description="The detected tone (e.g. 'corporate formal', 'friendly casual', 'technical expert')")
    audience_fit: str = Field(..., description="Assessment of whether tone matches target audience", max_length=200)
    issues: List[str] = Field(default_factory=list, description="Tone-related issues found", max_length=3)


class SkimTestAudit(BaseModel):
    """Analysis of whether headings tell a compelling story when skimmed"""
    skim_score: int = Field(..., ge=0, le=100, description="How well the heading hierarchy tells a story when skimmed (0-100)")
    story_assessment: str = Field(..., description="Assessment of the narrative flow from H1 through H2s", max_length=300)
    missing_beats: List[str] = Field(default_factory=list, description="Missing narrative beats in the heading structure", max_length=4)
    rewrite_suggestions: List[str] = Field(default_factory=list, description="Suggested heading rewrites for better skim flow", max_length=3)


class PageSemanticStrategy(BaseModel):
    """Complete semantic strategy analysis for a single page"""
    intent_gap: IntentGapAnalysis
    tone_audit: TonePersonaAudit
    skim_test: SkimTestAudit
    overall_strategy_score: int = Field(..., ge=0, le=100, description="Weighted average of the three sub-scores")
    top_recommendation: str = Field(..., description="Single most impactful recommendation for this page", max_length=300)
    suggested_title: Optional[str] = Field(None, description="Suggested title rewrite (5-8 words, keyword-front-loaded)")
    suggested_meta: Optional[str] = Field(None, description="Suggested meta description (two complete sentences)")


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