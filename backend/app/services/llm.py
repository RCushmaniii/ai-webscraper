import logging
import json
from typing import Dict, Any, List, Optional
import httpx
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM providers to generate summaries and insights."""
    
    def __init__(self, provider: str = None):
        """
        Initialize the LLM service.
        
        Args:
            provider: LLM provider to use (defaults to settings.LLM_PROVIDER)
        """
        self.provider = provider or settings.LLM_PROVIDER
        
        # Configure client based on provider
        if self.provider == "openai":
            self.api_key = settings.OPENAI_API_KEY
            self.model = settings.OPENAI_MODEL
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def generate_page_summary(self, page_data: Dict[str, Any]) -> str:
        """
        Generate a summary for a single page.
        
        Args:
            page_data: Page data including title, content, metadata
            
        Returns:
            Generated summary text
        """
        prompt = self._create_page_summary_prompt(page_data)
        return await self._generate_text(prompt)
    
    async def generate_site_audit(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive site audit based on crawl data.
        
        Args:
            crawl_data: Complete crawl data including pages, links, issues
            
        Returns:
            Dict containing audit sections and recommendations
        """
        prompt = self._create_site_audit_prompt(crawl_data)
        audit_text = await self._generate_text(prompt)
        
        try:
            # Parse the structured output
            return json.loads(audit_text)
        except json.JSONDecodeError:
            # Fallback if the LLM doesn't return valid JSON
            logger.warning("Failed to parse LLM output as JSON, returning raw text")
            return {
                "summary": audit_text,
                "structured_data": False
            }
    
    async def analyze_seo_issues(self, seo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze SEO data and identify issues with recommendations.
        
        Args:
            seo_data: SEO metadata for multiple pages
            
        Returns:
            List of SEO issues with recommendations
        """
        prompt = self._create_seo_analysis_prompt(seo_data)
        analysis_text = await self._generate_text(prompt)
        
        try:
            # Parse the structured output
            return json.loads(analysis_text)
        except json.JSONDecodeError:
            # Fallback if the LLM doesn't return valid JSON
            logger.warning("Failed to parse LLM output as JSON, returning default structure")
            return [{
                "issue": "Analysis format error",
                "description": analysis_text,
                "severity": "low",
                "recommendation": "Review the raw analysis text"
            }]
    
    async def _generate_text(self, prompt: str) -> str:
        """
        Generate text using the configured LLM provider.
        
        Args:
            prompt: Input prompt for the LLM
            
        Returns:
            Generated text response
        """
        if self.provider == "openai":
            return await self._generate_with_openai(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: Input prompt for the model
            
        Returns:
            Generated text response
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are an expert SEO and web analyst. Provide detailed, actionable insights based on web crawl data."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return f"Error generating content: {response.status_code}"
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return f"Error generating content: {str(e)}"
    
    def _create_page_summary_prompt(self, page_data: Dict[str, Any]) -> str:
        """Create a prompt for page summary generation."""
        return f"""
        Analyze this web page and provide a concise summary (3-5 sentences):
        
        URL: {page_data.get('url', 'Unknown')}
        Title: {page_data.get('title', 'Unknown')}
        
        Content excerpt:
        {page_data.get('text_content', '')[:1000]}
        
        SEO Metadata:
        - Meta Title: {page_data.get('seo_metadata', {}).get('title', 'None')}
        - Meta Description: {page_data.get('seo_metadata', {}).get('description', 'None')}
        - H1 Tags: {', '.join(page_data.get('seo_metadata', {}).get('h1_tags', [])[:3])}
        
        Focus on the main topic, purpose, and key information on this page.
        """
    
    def _create_site_audit_prompt(self, crawl_data: Dict[str, Any]) -> str:
        """Create a prompt for site audit generation."""
        # Calculate some statistics for the prompt
        total_pages = len(crawl_data.get('pages', []))
        internal_links = sum(1 for link in crawl_data.get('links', []) if link.get('is_internal', False))
        external_links = sum(1 for link in crawl_data.get('links', []) if not link.get('is_internal', True))
        broken_links = sum(1 for link in crawl_data.get('links', []) if link.get('is_broken', False))
        
        # Get top issues
        top_issues = crawl_data.get('issues', [])[:5]
        issues_text = "\n".join([f"- {issue.get('issue_type', 'Unknown')}: {issue.get('description', 'No description')}" for issue in top_issues])
        
        return f"""
        Generate a comprehensive site audit based on the following crawl data.
        
        Site Overview:
        - Total Pages: {total_pages}
        - Internal Links: {internal_links}
        - External Links: {external_links}
        - Broken Links: {broken_links}
        
        Top Issues:
        {issues_text}
        
        Provide your analysis in the following JSON format:
        {{
            "overview": "Overall assessment of the site",
            "strengths": ["Strength 1", "Strength 2", ...],
            "weaknesses": ["Weakness 1", "Weakness 2", ...],
            "seo_recommendations": ["Recommendation 1", "Recommendation 2", ...],
            "technical_recommendations": ["Recommendation 1", "Recommendation 2", ...],
            "content_recommendations": ["Recommendation 1", "Recommendation 2", ...],
            "priority_actions": ["Action 1", "Action 2", ...]
        }}
        
        Ensure your recommendations are specific, actionable, and prioritized.
        """
    
    def _create_seo_analysis_prompt(self, seo_data: Dict[str, Any]) -> str:
        """Create a prompt for SEO analysis."""
        # Prepare a summary of the SEO data
        pages_with_issues = []
        
        for page_url, metadata in seo_data.items():
            issues = []
            
            if not metadata.get('meta_title') or len(metadata.get('meta_title', '')) < 10:
                issues.append("Missing or short meta title")
            
            if not metadata.get('meta_description') or len(metadata.get('meta_description', '')) < 50:
                issues.append("Missing or short meta description")
            
            if not metadata.get('h1_tags'):
                issues.append("Missing H1 tag")
            
            if metadata.get('images_without_alt', 0) > 0:
                issues.append(f"{metadata.get('images_without_alt')} images missing alt text")
            
            if issues:
                pages_with_issues.append({
                    "url": page_url,
                    "issues": issues
                })
        
        # Create a summary of the top 5 pages with issues
        pages_summary = "\n".join([
            f"- URL: {page['url']}\n  Issues: {', '.join(page['issues'])}"
            for page in pages_with_issues[:5]
        ])
        
        return f"""
        Analyze the following SEO issues and provide recommendations.
        
        Pages with SEO Issues:
        {pages_summary}
        
        For each issue type, provide a detailed analysis and recommendation.
        Return your analysis in the following JSON format:
        [
            {{
                "issue": "Issue type (e.g., 'Missing meta descriptions')",
                "description": "Detailed description of the problem and its impact",
                "severity": "high|medium|low",
                "recommendation": "Specific recommendation to fix the issue",
                "affected_pages_count": Number of affected pages
            }},
            ...
        ]
        
        Focus on the most critical issues first and provide actionable recommendations.
        """

# Create a singleton instance
llm_service = LLMService()
