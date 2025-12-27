import asyncio
import hashlib
import httpx
import logging
import time
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright

from app.models.models import Crawl, Page, SEOMetadata, CrawlProgress, Link, Issue
from uuid import uuid4
from app.db.supabase import supabase_client
from app.core.config import settings
from app.services.storage import store_html_snapshot
from app.services.content_extractor import SmartContentExtractor

logger = logging.getLogger(__name__)

class Crawler:
    """
    Crawler service responsible for crawling websites and extracting data.
    Follows Single Responsibility Principle by focusing only on crawling logic.
    """
    
    def __init__(self, crawl: Crawl):
        self.crawl = crawl
        self.visited_urls: Set[str] = set()
        self.url_queue: List[Tuple[str, int, Optional[str]]] = []  # (url, depth, source_url)
        self.start_time = time.time()
        self.pages_crawled = 0
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers=self._get_headers()
        )
        self.rate_limiter = RateLimiter(self.crawl.rate_limit)
        self.domain = urlparse(self.crawl.url).netloc
        
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers based on the crawl's user agent setting."""
        default_user_agent = "AAA-WebScraper/1.0 (+https://example.com/bot)"
        
        return {
            "User-Agent": self.crawl.user_agent or default_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
    
    async def start(self) -> None:
        """Start the crawling process."""
        logger.info(f"Starting crawl for {self.crawl.url}")
        
        # Initialize the queue with the start URL
        self.url_queue.append((self.crawl.url, 0, None))
        
        # Process robots.txt and sitemaps if policy allows
        if self.crawl.respect_robots_txt:
            await self._process_robots_and_sitemaps()
        
        # Start crawling
        await self._crawl()
        
        # Close the HTTP client
        await self.client.aclose()
        
        logger.info(f"Crawl completed for {self.crawl.url}")
    
    async def _save_page_to_db(self, page: Page, seo_metadata: Optional[SEOMetadata]) -> None:
        """Save page and SEO metadata to database."""
        try:
            # Convert page to dict for Supabase - match actual schema
            page_data = {
                "id": str(page.id),
                "crawl_id": str(page.crawl_id),
                "url": page.url,
                "title": page.text_excerpt[:100] if page.text_excerpt else None,  # Use text excerpt as title
                "meta_description": None,  # Will extract later
                "content_summary": page.text_excerpt,
                "status_code": page.status_code,
                "response_time": page.render_ms,
                "content_type": page.content_type,
                "content_length": page.page_size_bytes,
                "h1_tags": [],  # Will extract later
                "h2_tags": [],  # Will extract later
                "internal_links": 0,  # Will count later
                "external_links": 0,  # Will count later
                "images": 0,  # Will count later
                "scripts": 0,  # Will count later
                "stylesheets": 0,  # Will count later
                "seo_score": 0,  # Will calculate later
                "issues": {}  # Will populate later
            }
            
            # Insert page
            result = supabase_client.table("pages").insert(page_data).execute()
            if hasattr(result, "error") and result.error:
                logger.error(f"Error saving page to database: {result.error}")
            else:
                logger.debug(f"Saved page {page.url} to database")
                
        except Exception as e:
            logger.error(f"Error saving page to database: {e}")
    
    async def _process_robots_and_sitemaps(self) -> None:
        """Process robots.txt and sitemaps to respect crawling rules and discover URLs."""
        parsed_url = urlparse(self.crawl.url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            # Fetch robots.txt
            await self.rate_limiter.wait()
            response = await self.client.get(robots_url)
            
            if response.status_code == 200:
                # Parse robots.txt (simplified)
                robots_content = response.text
                sitemap_urls = []
                
                for line in robots_content.split('\n'):
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemap_urls.append(sitemap_url)
                
                # Process sitemaps
                for sitemap_url in sitemap_urls:
                    await self._process_sitemap(sitemap_url)
        
        except Exception as e:
            logger.error(f"Error processing robots.txt: {e}")
    
    async def _process_sitemap(self, sitemap_url: str) -> None:
        """Process a sitemap to discover URLs."""
        try:
            await self.rate_limiter.wait()
            response = await self.client.get(sitemap_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                
                # Check if it's a sitemap index
                sitemap_tags = soup.find_all('sitemap')
                if sitemap_tags:
                    for sitemap_tag in sitemap_tags:
                        loc = sitemap_tag.find('loc')
                        if loc:
                            await self._process_sitemap(loc.text)
                else:
                    # Process URLs in the sitemap
                    url_tags = soup.find_all('url')
                    for url_tag in url_tags:
                        loc = url_tag.find('loc')
                        if loc:
                            url = loc.text
                            if self._should_crawl_url(url):
                                self.url_queue.append((url, 0, None))
        
        except Exception as e:
            logger.error(f"Error processing sitemap {sitemap_url}: {e}")
    
    async def _crawl(self) -> None:
        """Main crawling loop."""
        while self.url_queue and self.pages_crawled < self.crawl.max_pages:
            # Check if max runtime exceeded
            if time.time() - self.start_time > self.crawl.max_runtime_sec:
                logger.info("Max runtime exceeded, stopping crawl")
                break
            
            # Get the next URL from the queue
            url, depth, source_url = self.url_queue.pop(0)
            
            # Skip if already visited
            normalized_url = self._normalize_url(url)
            if normalized_url in self.visited_urls:
                continue
            
            self.visited_urls.add(normalized_url)
            
            # Crawl the URL
            try:
                page, seo_metadata = await self._crawl_url(url, depth, source_url)
                if page:
                    # Save page to database
                    await self._save_page_to_db(page, seo_metadata)
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
    
    async def _crawl_url(self, url: str, depth: int, source_url: Optional[str]) -> Tuple[Optional[Page], Optional[SEOMetadata]]:
        """Crawl a single URL."""
        logger.info(f"Crawling {url} at depth {depth}")
        
        # Wait for rate limiter
        await self.rate_limiter.wait()
        
        start_time = time.time()
        method = "html"
        
        try:
            # First try with regular HTTP request
            response = await self.client.get(url)
            final_url = str(response.url)
            status_code = response.status_code
            content_type = response.headers.get("content-type", "")

            # Check if we need to use Playwright for JavaScript rendering
            # Use JS rendering if explicitly enabled OR if auto-detection determines it's needed
            if self.crawl.js_rendering or self._needs_js_rendering(response):
                method = "js"
                html_content, render_time = await self._render_with_playwright(url)
            else:
                html_content = response.text
                render_time = int((time.time() - start_time) * 1000)
            
            # Calculate content hash
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()
            
            # Store HTML snapshot
            html_storage_path = await store_html_snapshot(
                self.crawl.id, 
                url, 
                html_content
            )
            
            # Use SmartContentExtractor for intelligent content analysis
            extractor = SmartContentExtractor(html_content, url)
            extracted_data = extractor.extract_all_data()
            
            # Extract basic text for backwards compatibility
            soup = BeautifulSoup(html_content, 'lxml')
            text_excerpt = extracted_data['content']['text'][:1000] if extracted_data['content']['text'] else self._extract_text_excerpt(soup)
            word_count = extracted_data['content']['word_count']
            
            # Create page record
            page = Page(
                crawl_id=self.crawl.id,
                url=url,
                final_url=final_url,
                status_code=status_code,
                method=method,
                render_ms=render_time,
                content_hash=content_hash,
                html_storage_path=html_storage_path,
                text_excerpt=text_excerpt,
                word_count=word_count,
                content_type=content_type,
                page_size_bytes=len(html_content)
            )
            
            # Use SmartContentExtractor for comprehensive SEO analysis
            seo_metadata = self._create_enhanced_seo_metadata(extracted_data, page.id)
            
            # Save comprehensive audit data
            await self._save_audit_data(page.id, extracted_data)
            
            # Extract links
            if status_code == 200:
                await self._extract_and_process_links(soup, url, depth, page.id)
            
            # Increment pages crawled
            self.pages_crawled += 1
            
            # Update crawl progress in database every 5 pages or on completion
            if self.pages_crawled % 5 == 0 or self.pages_crawled >= self.crawl.max_pages:
                await self._update_crawl_progress()
            
            # Return the page and metadata
            return page, seo_metadata
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            
            # Create a page record for the failed crawl
            page = Page(
                crawl_id=self.crawl.id,
                url=url,
                final_url=url,
                status_code=0,  # 0 indicates error
                method=method,
                render_ms=int((time.time() - start_time) * 1000),
                content_hash=None,
                html_storage_path=None,
                text_excerpt=f"Error: {str(e)}",
                word_count=0,
                content_type=None,
                page_size_bytes=0
            )
            
            # Create an issue record
            issue = Issue(
                crawl_id=self.crawl.id,
                page_id=page.id,
                type="crawl_error",
                severity="error",
                message=f"Failed to crawl URL: {str(e)}",
                context=url
            )
            
            return page, None
    
    def _needs_js_rendering(self, response: httpx.Response) -> bool:
        """Determine if a page needs JavaScript rendering."""
        # Check content type
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            return False
        
        # Check for empty or very small HTML
        if len(response.text) < 1000:
            return True
        
        # Check for common JS frameworks
        js_indicators = [
            "vue", "react", "angular", "ember", "backbone", 
            "data-reactroot", "ng-app", "v-app"
        ]
        
        for indicator in js_indicators:
            if indicator in response.text.lower():
                return True
        
        # Check for minimal HTML structure
        soup = BeautifulSoup(response.text, 'lxml')
        if len(soup.find_all(['p', 'div', 'section', 'article'])) < 5:
            return True
        
        return False
    
    async def _render_with_playwright(self, url: str) -> Tuple[str, int]:
        """Render a page with Playwright for JavaScript execution."""
        start_time = time.time()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                # Wait a bit more for any delayed JS execution
                await asyncio.sleep(2)
                html_content = await page.content()
                render_time = int((time.time() - start_time) * 1000)
            finally:
                await browser.close()
        
        return html_content, render_time
    
    def _extract_text_excerpt(self, soup: BeautifulSoup) -> str:
        """Extract meaningful text from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe", "svg"]):
            script.extract()
        
        # Get text and normalize whitespace
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit to 1000 characters
        return text[:1000] + ("..." if len(text) > 1000 else "")
    
    def _extract_seo_metadata(self, soup: BeautifulSoup, page_id: str) -> SEOMetadata:
        """Extract SEO metadata from HTML."""
        # Title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else None
        title_length = len(title) if title else 0
        
        # Meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag['content'].strip() if meta_desc_tag and 'content' in meta_desc_tag.attrs else None
        meta_description_length = len(meta_description) if meta_description else 0
        
        # H1
        h1_tag = soup.find('h1')
        h1 = h1_tag.text.strip() if h1_tag else None
        
        # H2s (first 5)
        h2_tags = soup.find_all('h2', limit=5)
        h2s = [tag.text.strip() for tag in h2_tags]
        
        # Robots meta
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        robots_meta = robots_tag['content'].strip() if robots_tag and 'content' in robots_tag.attrs else None
        
        # Canonical
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        canonical = canonical_tag['href'].strip() if canonical_tag and 'href' in canonical_tag.attrs else None
        
        # Hreflang
        hreflang_tags = soup.find_all('link', attrs={'rel': 'alternate', 'hreflang': True})
        hreflang = {}
        for tag in hreflang_tags:
            if 'href' in tag.attrs and 'hreflang' in tag.attrs:
                hreflang[tag['hreflang']] = tag['href']
        
        # Open Graph tags
        og_tags = {}
        for tag in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            if 'content' in tag.attrs:
                og_tags[tag['property']] = tag['content']
        
        # Twitter tags
        twitter_tags = {}
        for tag in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}):
            if 'content' in tag.attrs:
                twitter_tags[tag['name']] = tag['content']
        
        # JSON-LD
        json_ld = {}
        for script in soup.find_all('script', attrs={'type': 'application/ld+json'}):
            try:
                import json
                data = json.loads(script.string)
                json_ld = data
                break  # Just take the first one for now
            except:
                pass
        
        # Image alt text
        images = soup.find_all('img')
        image_alt_missing_count = sum(1 for img in images if not img.get('alt'))
        
        # Links
        links = soup.find_all('a', href=True)
        internal_links = 0
        external_links = 0
        
        for link in links:
            href = link['href']
            if href.startswith('#') or href.startswith('javascript:'):
                continue
                
            absolute_url = urljoin(self.crawl.url, href)
            parsed_url = urlparse(absolute_url)
            
            if parsed_url.netloc == self.domain:
                internal_links += 1
            else:
                external_links += 1
        
        return SEOMetadata(
            page_id=page_id,
            title=title,
            title_length=title_length,
            meta_description=meta_description,
            meta_description_length=meta_description_length,
            h1=h1,
            h2=h2s,
            robots_meta=robots_meta,
            hreflang=hreflang,
            canonical=canonical,
            og_tags=og_tags,
            twitter_tags=twitter_tags,
            json_ld=json_ld,
            image_alt_missing_count=image_alt_missing_count,
            internal_links=internal_links,
            external_links=external_links
        )
    
    async def _extract_and_process_links(
        self, 
        soup: BeautifulSoup, 
        source_url: str, 
        depth: int, 
        source_page_id: str
    ) -> None:
        """Extract links from HTML and process them."""
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            
            # Skip fragment-only and javascript links
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Convert to absolute URL
            absolute_url = urljoin(source_url, href)
            parsed_url = urlparse(absolute_url)
            
            # Determine if internal or external
            is_internal = parsed_url.netloc == self.domain
            
            # Check if we should follow this link
            should_follow = False
            new_depth = depth + 1
            
            if is_internal and new_depth <= self.crawl.internal_depth:
                should_follow = True
            elif not is_internal and self.crawl.follow_external and new_depth <= self.crawl.external_depth:
                should_follow = True
            
            # Create link record matching database schema
            link_data = {
                "id": str(uuid4()),
                "crawl_id": str(self.crawl.id),
                "source_page_id": str(source_page_id),
                "target_url": absolute_url,
                "is_internal": is_internal,
                "depth": new_depth,
                "status_code": None,
                "error": None,
                "latency_ms": None,
                "anchor_text": link.text.strip()[:500] if link.text else None,  # Limit length
                "is_nofollow": link.get('rel') and 'nofollow' in link.get('rel', []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Check link status (async)
            if should_follow:
                # Add to queue for crawling
                self.url_queue.append((absolute_url, new_depth, source_url))
                # Save link without status check
                await self._save_link(link_data)
            else:
                # Check status and save with status info
                await self._check_and_save_link(link_data)
    
    async def _save_link(self, link_data: Dict) -> None:
        """Save a link to the database."""
        try:
            result = supabase_client.table("links").insert(link_data).execute()
            if hasattr(result, "error") and result.error:
                logger.error(f"Error saving link: {result.error}")
            else:
                logger.debug(f"Saved link {link_data['target_url'][:100]}")
        except Exception as e:
            logger.error(f"Error saving link: {e}")

    async def _check_and_save_link(self, link_data: Dict) -> None:
        """Check link status and save to database."""
        try:
            await self.rate_limiter.wait()
            start_time = time.time()

            # Try HEAD request first
            try:
                response = await self.client.head(
                    link_data['target_url'],
                    follow_redirects=True,
                    timeout=10.0
                )
                link_data['status_code'] = response.status_code
                link_data['latency_ms'] = int((time.time() - start_time) * 1000)
            except Exception:
                # If HEAD fails, try GET
                try:
                    response = await self.client.get(
                        link_data['target_url'],
                        follow_redirects=True,
                        timeout=10.0
                    )
                    link_data['status_code'] = response.status_code
                    link_data['latency_ms'] = int((time.time() - start_time) * 1000)
                except Exception as e:
                    link_data['status_code'] = 0
                    link_data['error'] = str(e)[:500]  # Limit error length
                    link_data['latency_ms'] = int((time.time() - start_time) * 1000)

            # Save the link with status info
            await self._save_link(link_data)

        except Exception as e:
            logger.error(f"Error checking and saving link: {e}")
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates."""
        parsed = urlparse(url)
        
        # Convert to lowercase
        netloc = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Remove trailing slash from path if present
        if path.endswith('/'):
            path = path[:-1]
        
        # Add slash if path is empty
        if not path:
            path = '/'
        
        # Remove default ports
        if (parsed.scheme == 'http' and netloc.endswith(':80')) or (parsed.scheme == 'https' and netloc.endswith(':443')):
            netloc = netloc.rsplit(':', 1)[0]
        
        # Reconstruct URL without fragments and some query params
        query = parsed.query
        if query:
            # Remove tracking parameters
            tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'fbclid', 'gclid'}
            query_parts = []
            
            for param in query.split('&'):
                if '=' in param:
                    name, value = param.split('=', 1)
                    if name.lower() not in tracking_params:
                        query_parts.append(f"{name}={value}")
                else:
                    query_parts.append(param)
            
            query = '&'.join(query_parts)
        
        return f"{parsed.scheme}://{netloc}{path}{'?' + query if query else ''}"
    
    def _should_crawl_url(self, url: str) -> bool:
        """Determine if a URL should be crawled based on rules."""
        parsed = urlparse(url)
        
        # Skip non-HTTP(S) URLs
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Check file extensions to skip
        skip_extensions = {
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
            '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.css', '.js'
        }
        
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        return True
    
    def get_progress(self) -> CrawlProgress:
        """Get the current progress of the crawl."""
        elapsed_time = time.time() - self.start_time
        progress_percentage = (self.pages_crawled / self.crawl.max_pages) * 100 if self.crawl.max_pages > 0 else 0
        
        # Estimate remaining time
        estimated_time_remaining = None
        if progress_percentage > 0:
            estimated_time_remaining = int((elapsed_time / progress_percentage) * (100 - progress_percentage))
        
        return CrawlProgress(
            crawl_id=self.crawl.id,
            status="in_progress" if self.url_queue else "completed",
            pages_crawled=self.pages_crawled,
            total_pages=self.crawl.max_pages,
            current_url=self.url_queue[0][0] if self.url_queue else None,
            progress_percentage=progress_percentage,
            elapsed_time_seconds=int(elapsed_time),
            estimated_time_remaining_seconds=estimated_time_remaining
        )
    
    def _create_enhanced_seo_metadata(self, extracted_data: Dict, page_id: str) -> SEOMetadata:
        """Create enhanced SEO metadata using SmartContentExtractor data."""
        seo_data = extracted_data['seo']
        technical_data = extracted_data['technical']
        
        return SEOMetadata(
            page_id=page_id,
            title=seo_data.get('title'),
            title_length=seo_data.get('title_length', 0),
            meta_description=seo_data.get('meta_description'),
            meta_description_length=seo_data.get('description_length', 0),
            h1=extracted_data['content']['headings'][0]['text'] if extracted_data['content']['headings'] and extracted_data['content']['headings'][0]['level'] == 1 else None,
            h2=[h['text'] for h in extracted_data['content']['headings'] if h['level'] == 2][:5],
            robots_meta=seo_data.get('robots'),
            hreflang={},  # Will enhance later
            canonical=seo_data.get('canonical'),
            og_tags={
                'og:title': seo_data.get('og_title'),
                'og:description': seo_data.get('og_description'),
                'og:image': seo_data.get('og_image')
            },
            twitter_tags={},  # Will enhance later
            json_ld=seo_data.get('schema_markup', {}) if isinstance(seo_data.get('schema_markup'), dict) else {},
            image_alt_missing_count=technical_data.get('images_without_alt', 0),
            internal_links=technical_data.get('internal_links', 0),
            external_links=technical_data.get('external_links', 0)
        )
    
    async def _save_audit_data(self, page_id: str, extracted_data: Dict) -> None:
        """Save comprehensive audit data to database."""
        try:
            # Save SEO audit data
            seo_audit = {
                'page_id': page_id,
                'crawl_id': str(self.crawl.id),
                'title_issues': self._analyze_title_issues(extracted_data['seo']),
                'meta_description_issues': self._analyze_meta_description_issues(extracted_data['seo']),
                'heading_issues': self._analyze_heading_issues(extracted_data['content']['headings']),
                'image_issues': self._analyze_image_issues(extracted_data['images']),
                'content_quality_score': self._calculate_content_quality_score(extracted_data),
                'seo_score': self._calculate_seo_score(extracted_data),
                'technical_issues': self._identify_technical_issues(extracted_data['technical']),
                'created_at': datetime.now().isoformat()
            }
            
            # Insert SEO audit data
            result = supabase_client.table("seo_audits").insert(seo_audit).execute()
            if hasattr(result, "error") and result.error:
                logger.error(f"Error saving SEO audit data: {result.error}")
            
            # Save individual issues for detailed reporting
            issues = self._generate_issues_list(page_id, extracted_data)
            if issues:
                result = supabase_client.table("issues").insert(issues).execute()
                if hasattr(result, "error") and result.error:
                    logger.error(f"Error saving issues: {result.error}")
                    
        except Exception as e:
            logger.error(f"Error saving audit data: {e}")
    
    def _analyze_title_issues(self, seo_data: Dict) -> List[str]:
        """Analyze title tag issues."""
        issues = []
        title = seo_data.get('title', '')
        title_length = seo_data.get('title_length', 0)
        
        if not title:
            issues.append('Missing title tag')
        elif title_length < 30:
            issues.append('Title too short (< 30 characters)')
        elif title_length > 60:
            issues.append('Title too long (> 60 characters)')
        
        return issues
    
    def _analyze_meta_description_issues(self, seo_data: Dict) -> List[str]:
        """Analyze meta description issues."""
        issues = []
        description = seo_data.get('meta_description', '')
        description_length = seo_data.get('description_length', 0)
        
        if not description:
            issues.append('Missing meta description')
        elif description_length < 120:
            issues.append('Meta description too short (< 120 characters)')
        elif description_length > 160:
            issues.append('Meta description too long (> 160 characters)')
        
        return issues
    
    def _analyze_heading_issues(self, headings: List[Dict]) -> List[str]:
        """Analyze heading structure issues."""
        issues = []
        h1_count = len([h for h in headings if h['level'] == 1])
        
        if h1_count == 0:
            issues.append('Missing H1 tag')
        elif h1_count > 1:
            issues.append(f'Multiple H1 tags found ({h1_count})')
        
        # Check heading hierarchy
        prev_level = 0
        for heading in headings:
            level = heading['level']
            if level > prev_level + 1:
                issues.append(f'Heading hierarchy skip: H{prev_level} to H{level}')
            prev_level = level
        
        return issues
    
    def _analyze_image_issues(self, images: List[Dict]) -> List[str]:
        """Analyze image-related issues."""
        issues = []
        total_images = len(images)
        images_without_alt = len([img for img in images if not img.get('has_alt')])
        
        if images_without_alt > 0:
            issues.append(f'{images_without_alt} images missing alt text')
        
        return issues
    
    def _calculate_content_quality_score(self, extracted_data: Dict) -> int:
        """Calculate content quality score (0-100)."""
        score = 100
        content = extracted_data['content']
        
        # Word count scoring
        word_count = content.get('word_count', 0)
        if word_count < 300:
            score -= 20
        elif word_count < 500:
            score -= 10
        
        # Reading time scoring
        reading_time = content.get('reading_time', 0)
        if reading_time < 2:
            score -= 15
        
        # Heading structure scoring
        headings = content.get('headings', [])
        if not headings:
            score -= 25
        
        return max(0, score)
    
    def _calculate_seo_score(self, extracted_data: Dict) -> int:
        """Calculate SEO score (0-100)."""
        score = 100
        seo_data = extracted_data['seo']
        technical_data = extracted_data['technical']
        
        # Title issues
        if not seo_data.get('title'):
            score -= 20
        elif seo_data.get('title_length', 0) > 60:
            score -= 10
        
        # Meta description issues
        if not seo_data.get('meta_description'):
            score -= 15
        elif seo_data.get('description_length', 0) > 160:
            score -= 5
        
        # H1 issues
        h1_count = technical_data.get('h1_count', 0)
        if h1_count == 0:
            score -= 15
        elif h1_count > 1:
            score -= 10
        
        # Image alt text issues
        images_without_alt = technical_data.get('images_without_alt', 0)
        if images_without_alt > 0:
            score -= min(20, images_without_alt * 2)
        
        return max(0, score)
    
    def _identify_technical_issues(self, technical_data: Dict) -> List[str]:
        """Identify technical SEO issues."""
        issues = []
        
        if not technical_data.get('has_viewport_meta'):
            issues.append('Missing viewport meta tag')
        
        if not technical_data.get('has_lang_attribute'):
            issues.append('Missing lang attribute on html tag')
        
        page_size_kb = technical_data.get('page_size_kb', 0)
        if page_size_kb > 1000:  # 1MB
            issues.append(f'Large page size: {page_size_kb:.1f}KB')
        
        return issues
    
    def _generate_issues_list(self, page_id: str, extracted_data: Dict) -> List[Dict]:
        """Generate a list of issues for the issues table."""
        issues = []
        
        # Title issues
        title_issues = self._analyze_title_issues(extracted_data['seo'])
        for issue in title_issues:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': page_id,
                'type': 'SEO',
                'severity': 'high' if 'Missing' in issue else 'medium',
                'message': issue,
                'pointer': None,
                'context': extracted_data.get('url', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })

        # Meta description issues
        meta_issues = self._analyze_meta_description_issues(extracted_data['seo'])
        for issue in meta_issues:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': page_id,
                'type': 'SEO',
                'severity': 'high' if 'Missing' in issue else 'medium',
                'message': issue,
                'pointer': None,
                'context': extracted_data.get('url', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })

        # Heading issues
        heading_issues = self._analyze_heading_issues(extracted_data['content']['headings'])
        for issue in heading_issues:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': page_id,
                'type': 'SEO',
                'severity': 'high' if 'Missing H1' in issue else 'medium',
                'message': issue,
                'pointer': None,
                'context': extracted_data.get('url', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })

        # Technical issues
        technical_issues = self._identify_technical_issues(extracted_data['technical'])
        for issue in technical_issues:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': page_id,
                'type': 'Technical',
                'severity': 'low' if 'Large page size' in issue else 'medium',
                'message': issue,
                'pointer': None,
                'context': extracted_data.get('url', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return issues

    async def _update_crawl_progress(self) -> None:
        """Update crawl progress in the database."""
        try:
            # Count total links discovered so far
            total_links = len(self.visited_urls) + len(self.url_queue)
            
            # Update crawl record with current progress
            update_data = {
                "pages_crawled": self.pages_crawled,
                "total_links": total_links,
                "updated_at": datetime.now().isoformat()
            }
            
            result = supabase_client.table("crawls").update(update_data).eq("id", str(self.crawl.id)).execute()
            
            if hasattr(result, "error") and result.error:
                logger.error(f"Error updating crawl progress: {result.error}")
            else:
                logger.debug(f"Updated crawl progress: {self.pages_crawled} pages, {total_links} links")
                
        except Exception as e:
            logger.error(f"Error updating crawl progress: {e}")


class RateLimiter:
    """Rate limiter to control request frequency."""
    
    def __init__(self, requests_per_second: float):
        self.delay = 1.0 / requests_per_second
        self.last_request_time = 0
    
    async def wait(self) -> None:
        """Wait if needed to maintain the rate limit."""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        
        self.last_request_time = time.time()
