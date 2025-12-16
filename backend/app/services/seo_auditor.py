# backend/app/services/seo_auditor.py
import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import re

from app.services.content_extractor import SmartContentExtractor
from app.db.supabase import supabase_client
from uuid import uuid4

logger = logging.getLogger(__name__)

class SEOAuditor:
    """
    Advanced SEO auditing service that provides comprehensive website analysis.
    Delivers clear business value through actionable insights.
    """
    
    def __init__(self, crawl_id: str):
        self.crawl_id = crawl_id
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run a comprehensive SEO audit for the crawl."""
        logger.info(f"Starting comprehensive SEO audit for crawl {self.crawl_id}")
        
        audit_results = {
            'crawl_id': self.crawl_id,
            'audit_date': datetime.now().isoformat(),
            'broken_links': await self._audit_broken_links(),
            'content_freshness': await self._audit_content_freshness(),
            'duplicate_content': await self._audit_duplicate_content(),
            'missing_schema': await self._audit_missing_schema(),
            'performance_issues': await self._audit_performance_issues(),
            'mobile_issues': await self._audit_mobile_readiness(),
            'overall_score': 0,
            'priority_issues': [],
            'recommendations': []
        }
        
        # Calculate overall score and generate recommendations
        audit_results['overall_score'] = self._calculate_overall_score(audit_results)
        audit_results['priority_issues'] = self._identify_priority_issues(audit_results)
        audit_results['recommendations'] = self._generate_recommendations(audit_results)
        
        # Save audit results
        await self._save_audit_results(audit_results)
        
        await self.client.aclose()
        return audit_results
    
    async def _audit_broken_links(self) -> Dict[str, Any]:
        """Comprehensive broken link detection and analysis."""
        logger.info("Auditing broken links...")
        
        try:
            # Get all links for this crawl
            response = supabase_client.table("links").select("*").eq("crawl_id", self.crawl_id).execute()
            links = response.data if response.data else []
            
            broken_links = []
            redirect_chains = []
            external_broken = []
            
            for link in links:
                if link.get('is_broken') or not link.get('status_code') or link.get('status_code') >= 400:
                    link_info = {
                        'url': link['target_url'],
                        'source_pages': [link['source_url']],
                        'status_code': link.get('status_code', 0),
                        'error': link.get('error_message', 'Unknown error'),
                        'is_internal': link.get('is_internal', False)
                    }
                    
                    if link.get('is_internal'):
                        broken_links.append(link_info)
                    else:
                        external_broken.append(link_info)
                
                # Check for redirect chains
                if link.get('status_code') in [301, 302, 307, 308]:
                    redirect_chains.append({
                        'url': link['target_url'],
                        'status_code': link['status_code'],
                        'source_page': link['source_url']
                    })
            
            return {
                'total_broken_internal': len(broken_links),
                'total_broken_external': len(external_broken),
                'total_redirects': len(redirect_chains),
                'broken_internal_links': broken_links[:20],  # Limit for performance
                'broken_external_links': external_broken[:20],
                'redirect_chains': redirect_chains[:10],
                'impact_score': min(100, (len(broken_links) * 5) + (len(external_broken) * 2))
            }
            
        except Exception as e:
            logger.error(f"Error auditing broken links: {e}")
            return {'error': str(e), 'impact_score': 0}
    
    async def _audit_content_freshness(self) -> Dict[str, Any]:
        """Audit content freshness and identify stale pages."""
        logger.info("Auditing content freshness...")
        
        try:
            # Get all pages for this crawl
            response = supabase_client.table("pages").select("*").eq("crawl_id", self.crawl_id).execute()
            pages = response.data if response.data else []
            
            stale_pages = []
            outdated_pages = []
            current_date = datetime.now()
            
            for page in pages:
                # Check for date indicators in content
                freshness_score = await self._analyze_page_freshness(page)
                
                if freshness_score['days_since_update'] > 365:  # 1 year
                    stale_pages.append({
                        'url': page['url'],
                        'title': page.get('title', 'No title'),
                        'days_since_update': freshness_score['days_since_update'],
                        'last_modified': freshness_score.get('last_modified'),
                        'content_indicators': freshness_score.get('date_indicators', [])
                    })
                elif freshness_score['days_since_update'] > 180:  # 6 months
                    outdated_pages.append({
                        'url': page['url'],
                        'title': page.get('title', 'No title'),
                        'days_since_update': freshness_score['days_since_update'],
                        'last_modified': freshness_score.get('last_modified')
                    })
            
            return {
                'total_stale_pages': len(stale_pages),
                'total_outdated_pages': len(outdated_pages),
                'stale_pages': stale_pages[:15],
                'outdated_pages': outdated_pages[:15],
                'freshness_score': max(0, 100 - (len(stale_pages) * 10) - (len(outdated_pages) * 5)),
                'recommendations': self._generate_freshness_recommendations(stale_pages, outdated_pages)
            }
            
        except Exception as e:
            logger.error(f"Error auditing content freshness: {e}")
            return {'error': str(e), 'freshness_score': 0}
    
    async def _analyze_page_freshness(self, page: Dict) -> Dict[str, Any]:
        """Analyze individual page freshness indicators."""
        try:
            # Try to get HTML content and analyze for date indicators
            html_path = page.get('html_snapshot_path')
            if not html_path:
                return {'days_since_update': 999, 'confidence': 'low'}
            
            # For now, use creation date as fallback
            # In a real implementation, you'd analyze the HTML content for:
            # - Last modified dates
            # - Copyright years
            # - News article dates
            # - Blog post dates
            # - "Updated on" text
            
            created_at = page.get('created_at')
            if created_at:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_since = (datetime.now() - created_date).days
                return {
                    'days_since_update': days_since,
                    'confidence': 'medium',
                    'last_modified': created_at,
                    'date_indicators': []
                }
            
            return {'days_since_update': 999, 'confidence': 'low'}
            
        except Exception as e:
            logger.error(f"Error analyzing page freshness: {e}")
            return {'days_since_update': 999, 'confidence': 'low'}
    
    async def _audit_duplicate_content(self) -> Dict[str, Any]:
        """Detect duplicate and near-duplicate content."""
        logger.info("Auditing duplicate content...")
        
        try:
            # Get all pages with content hashes
            response = supabase_client.table("pages").select("url, title, content_hash, content_summary").eq("crawl_id", self.crawl_id).execute()
            pages = response.data if response.data else []
            
            # Group by content hash
            hash_groups = {}
            title_groups = {}
            
            for page in pages:
                content_hash = page.get('content_hash')
                title = page.get('title', '').strip().lower()
                
                if content_hash:
                    if content_hash not in hash_groups:
                        hash_groups[content_hash] = []
                    hash_groups[content_hash].append(page)
                
                if title and len(title) > 10:  # Ignore very short titles
                    if title not in title_groups:
                        title_groups[title] = []
                    title_groups[title].append(page)
            
            # Find duplicates
            duplicate_content = []
            duplicate_titles = []
            
            for hash_val, pages_list in hash_groups.items():
                if len(pages_list) > 1:
                    duplicate_content.append({
                        'content_hash': hash_val,
                        'pages': [{'url': p['url'], 'title': p.get('title', 'No title')} for p in pages_list],
                        'count': len(pages_list)
                    })
            
            for title, pages_list in title_groups.items():
                if len(pages_list) > 1:
                    duplicate_titles.append({
                        'title': title,
                        'pages': [{'url': p['url']} for p in pages_list],
                        'count': len(pages_list)
                    })
            
            return {
                'duplicate_content_groups': len(duplicate_content),
                'duplicate_title_groups': len(duplicate_titles),
                'duplicate_content': duplicate_content[:10],
                'duplicate_titles': duplicate_titles[:10],
                'impact_score': (len(duplicate_content) * 15) + (len(duplicate_titles) * 10)
            }
            
        except Exception as e:
            logger.error(f"Error auditing duplicate content: {e}")
            return {'error': str(e), 'impact_score': 0}
    
    async def _audit_missing_schema(self) -> Dict[str, Any]:
        """Audit for missing structured data and schema markup."""
        logger.info("Auditing schema markup...")
        
        try:
            # Get SEO metadata for all pages
            response = supabase_client.table("seo_metadata").select("*").eq("crawl_id", self.crawl_id).execute()
            seo_data = response.data if response.data else []
            
            pages_without_schema = []
            schema_types_found = set()
            
            for seo_record in seo_data:
                json_ld = seo_record.get('json_ld', {})
                page_url = seo_record.get('page_url', 'Unknown')
                
                if not json_ld or (isinstance(json_ld, dict) and not json_ld):
                    pages_without_schema.append({
                        'url': page_url,
                        'page_type': self._detect_page_type(page_url)
                    })
                else:
                    # Extract schema types
                    if isinstance(json_ld, dict):
                        schema_type = json_ld.get('@type', 'Unknown')
                        schema_types_found.add(schema_type)
            
            return {
                'pages_without_schema': len(pages_without_schema),
                'schema_types_found': list(schema_types_found),
                'missing_schema_pages': pages_without_schema[:15],
                'schema_coverage': max(0, 100 - (len(pages_without_schema) * 5)),
                'recommendations': self._generate_schema_recommendations(pages_without_schema)
            }
            
        except Exception as e:
            logger.error(f"Error auditing schema markup: {e}")
            return {'error': str(e), 'schema_coverage': 0}
    
    async def _audit_performance_issues(self) -> Dict[str, Any]:
        """Audit performance-related issues."""
        logger.info("Auditing performance issues...")
        
        try:
            response = supabase_client.table("pages").select("url, response_time, content_length, title").eq("crawl_id", self.crawl_id).execute()
            pages = response.data if response.data else []
            
            slow_pages = []
            large_pages = []
            
            for page in pages:
                response_time = page.get('response_time', 0)
                content_length = page.get('content_length', 0)
                
                if response_time > 3000:  # 3 seconds
                    slow_pages.append({
                        'url': page['url'],
                        'title': page.get('title', 'No title'),
                        'response_time': response_time,
                        'severity': 'high' if response_time > 5000 else 'medium'
                    })
                
                if content_length > 1024 * 1024:  # 1MB
                    large_pages.append({
                        'url': page['url'],
                        'title': page.get('title', 'No title'),
                        'size_mb': round(content_length / (1024 * 1024), 2),
                        'severity': 'high' if content_length > 2 * 1024 * 1024 else 'medium'
                    })
            
            avg_response_time = sum(p.get('response_time', 0) for p in pages) / len(pages) if pages else 0
            
            return {
                'slow_pages_count': len(slow_pages),
                'large_pages_count': len(large_pages),
                'average_response_time': round(avg_response_time, 2),
                'slow_pages': slow_pages[:10],
                'large_pages': large_pages[:10],
                'performance_score': max(0, 100 - (len(slow_pages) * 10) - (len(large_pages) * 5))
            }
            
        except Exception as e:
            logger.error(f"Error auditing performance: {e}")
            return {'error': str(e), 'performance_score': 0}
    
    async def _audit_mobile_readiness(self) -> Dict[str, Any]:
        """Audit mobile readiness indicators."""
        logger.info("Auditing mobile readiness...")
        
        try:
            # Check for viewport meta tags and responsive indicators
            response = supabase_client.table("seo_audits").select("*").eq("crawl_id", self.crawl_id).execute()
            audits = response.data if response.data else []
            
            pages_without_viewport = 0
            mobile_issues = []
            
            for audit in audits:
                technical_issues = audit.get('technical_issues', [])
                
                for issue in technical_issues:
                    if 'viewport' in issue.lower():
                        pages_without_viewport += 1
                        mobile_issues.append({
                            'page_id': audit.get('page_id'),
                            'issue': issue,
                            'severity': 'high'
                        })
            
            mobile_score = max(0, 100 - (pages_without_viewport * 20))
            
            return {
                'pages_without_viewport': pages_without_viewport,
                'mobile_issues': mobile_issues[:10],
                'mobile_score': mobile_score,
                'recommendations': [
                    'Add viewport meta tag to all pages',
                    'Test responsive design on mobile devices',
                    'Optimize touch targets for mobile interaction'
                ] if pages_without_viewport > 0 else []
            }
            
        except Exception as e:
            logger.error(f"Error auditing mobile readiness: {e}")
            return {'error': str(e), 'mobile_score': 0}
    
    def _detect_page_type(self, url: str) -> str:
        """Detect the type of page based on URL patterns."""
        url_lower = url.lower()
        
        if '/blog/' in url_lower or '/news/' in url_lower or '/article/' in url_lower:
            return 'Article'
        elif '/product/' in url_lower or '/shop/' in url_lower:
            return 'Product'
        elif '/about' in url_lower:
            return 'AboutPage'
        elif '/contact' in url_lower:
            return 'ContactPage'
        elif url_lower.endswith('/') or url_lower.split('/')[-1] == '':
            return 'WebPage'
        else:
            return 'WebPage'
    
    def _generate_freshness_recommendations(self, stale_pages: List, outdated_pages: List) -> List[str]:
        """Generate content freshness recommendations."""
        recommendations = []
        
        if stale_pages:
            recommendations.append(f"Update {len(stale_pages)} stale pages (>1 year old)")
            recommendations.append("Add 'Last Updated' dates to content")
            recommendations.append("Implement content review schedule")
        
        if outdated_pages:
            recommendations.append(f"Review {len(outdated_pages)} outdated pages (>6 months old)")
            recommendations.append("Create content maintenance calendar")
        
        return recommendations
    
    def _generate_schema_recommendations(self, pages_without_schema: List) -> List[str]:
        """Generate schema markup recommendations."""
        recommendations = []
        
        if pages_without_schema:
            page_types = {}
            for page in pages_without_schema:
                page_type = page.get('page_type', 'WebPage')
                page_types[page_type] = page_types.get(page_type, 0) + 1
            
            for page_type, count in page_types.items():
                recommendations.append(f"Add {page_type} schema to {count} pages")
        
        return recommendations
    
    def _calculate_overall_score(self, audit_results: Dict) -> int:
        """Calculate overall SEO audit score."""
        scores = []
        
        # Collect all scores
        if 'broken_links' in audit_results and 'impact_score' in audit_results['broken_links']:
            scores.append(max(0, 100 - audit_results['broken_links']['impact_score']))
        
        if 'content_freshness' in audit_results and 'freshness_score' in audit_results['content_freshness']:
            scores.append(audit_results['content_freshness']['freshness_score'])
        
        if 'missing_schema' in audit_results and 'schema_coverage' in audit_results['missing_schema']:
            scores.append(audit_results['missing_schema']['schema_coverage'])
        
        if 'performance_issues' in audit_results and 'performance_score' in audit_results['performance_issues']:
            scores.append(audit_results['performance_issues']['performance_score'])
        
        if 'mobile_issues' in audit_results and 'mobile_score' in audit_results['mobile_issues']:
            scores.append(audit_results['mobile_issues']['mobile_score'])
        
        return round(sum(scores) / len(scores)) if scores else 0
    
    def _identify_priority_issues(self, audit_results: Dict) -> List[Dict]:
        """Identify high-priority issues requiring immediate attention."""
        priority_issues = []
        
        # Broken links
        broken_links = audit_results.get('broken_links', {})
        if broken_links.get('total_broken_internal', 0) > 0:
            priority_issues.append({
                'type': 'Broken Links',
                'severity': 'high',
                'count': broken_links['total_broken_internal'],
                'description': f"{broken_links['total_broken_internal']} broken internal links found",
                'impact': 'Hurts user experience and SEO rankings'
            })
        
        # Stale content
        freshness = audit_results.get('content_freshness', {})
        if freshness.get('total_stale_pages', 0) > 5:
            priority_issues.append({
                'type': 'Stale Content',
                'severity': 'medium',
                'count': freshness['total_stale_pages'],
                'description': f"{freshness['total_stale_pages']} pages haven't been updated in over a year",
                'impact': 'Reduces content relevance and search rankings'
            })
        
        # Missing schema
        schema = audit_results.get('missing_schema', {})
        if schema.get('pages_without_schema', 0) > 10:
            priority_issues.append({
                'type': 'Missing Schema',
                'severity': 'medium',
                'count': schema['pages_without_schema'],
                'description': f"{schema['pages_without_schema']} pages missing structured data",
                'impact': 'Missed opportunities for rich snippets'
            })
        
        return priority_issues
    
    def _generate_recommendations(self, audit_results: Dict) -> List[str]:
        """Generate actionable recommendations based on audit results."""
        recommendations = []
        
        # High-priority recommendations
        broken_links = audit_results.get('broken_links', {})
        if broken_links.get('total_broken_internal', 0) > 0:
            recommendations.append("🔴 Fix broken internal links immediately - they hurt user experience")
        
        freshness = audit_results.get('content_freshness', {})
        if freshness.get('total_stale_pages', 0) > 0:
            recommendations.append("📅 Update stale content - fresh content ranks better")
        
        # Medium-priority recommendations
        schema = audit_results.get('missing_schema', {})
        if schema.get('pages_without_schema', 0) > 0:
            recommendations.append("📊 Add structured data for better search visibility")
        
        performance = audit_results.get('performance_issues', {})
        if performance.get('slow_pages_count', 0) > 0:
            recommendations.append("⚡ Optimize page load times - speed affects rankings")
        
        mobile = audit_results.get('mobile_issues', {})
        if mobile.get('pages_without_viewport', 0) > 0:
            recommendations.append("📱 Add viewport meta tags for mobile optimization")
        
        return recommendations
    
    async def _save_audit_results(self, audit_results: Dict) -> None:
        """Save comprehensive audit results to database."""
        try:
            result = supabase_client.table("comprehensive_audits").insert({
                'id': str(uuid4()),
                'crawl_id': self.crawl_id,
                'audit_data': audit_results,
                'overall_score': audit_results['overall_score'],
                'priority_issues_count': len(audit_results['priority_issues']),
                'created_at': datetime.now().isoformat()
            }).execute()
            
            if hasattr(result, "error") and result.error:
                logger.error(f"Error saving audit results: {result.error}")
            else:
                logger.info(f"Saved comprehensive audit results for crawl {self.crawl_id}")
                
        except Exception as e:
            logger.error(f"Error saving audit results: {e}")
