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

    def __init__(self, crawl: Crawl, db_client=None):
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
        # Use provided db_client (service role) or fall back to default (anon)
        self.db = db_client if db_client is not None else supabase_client
        self.crawl_deleted = False  # Track if crawl was deleted during processing
        
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
        
        # Verify crawl exists before starting
        if not await self._verify_crawl_exists():
            logger.warning(f"Crawl {self.crawl.id} was deleted before starting. Exiting gracefully.")
            return
        
        # Initialize the queue with the start URL
        self.url_queue.append((self.crawl.url, 0, None))
        
        # Process robots.txt and sitemaps if policy allows
        if self.crawl.respect_robots_txt:
            await self._process_robots_and_sitemaps()
        
        # Start crawling
        await self._crawl()
        
        # Close the HTTP client
        await self.client.aclose()
        
        if self.crawl_deleted:
            logger.info(f"Crawl {self.crawl.id} was deleted during processing. Stopped gracefully.")
        else:
            logger.info(f"Crawl completed for {self.crawl.url}")
    
    async def _save_page_to_db(self, page: Page, seo_metadata: Optional[SEOMetadata]) -> None:
        """Save page and SEO metadata to database."""
        try:
            # Use actual SEO metadata if available, otherwise use defaults
            if seo_metadata:
                title = seo_metadata.title or "No title found"
                meta_description = seo_metadata.meta_description
                h1_tags = [seo_metadata.h1] if seo_metadata.h1 else []
                h2_tags = seo_metadata.h2 or []
                internal_links_count = seo_metadata.internal_links
                external_links_count = seo_metadata.external_links
            else:
                title = page.url
                meta_description = None
                h1_tags = []
                h2_tags = []
                internal_links_count = 0
                external_links_count = 0

            # Convert page to dict for Supabase - MATCH EXACT DATABASE SCHEMA
            # NOTE: Images count will be 0 initially, updated later after images are saved
            page_data = {
                "id": str(page.id),
                "crawl_id": str(page.crawl_id),
                "url": page.url,
                "title": title,  # REAL title from SEO metadata
                "meta_description": meta_description,  # REAL meta description
                "content_summary": page.text_excerpt,  # 5000 char excerpt for preview
                "status_code": page.status_code,
                "response_time": page.render_ms,
                "content_type": page.content_type,
                "content_length": page.page_size_bytes,
                "h1_tags": h1_tags,  # REAL H1 tags
                "h2_tags": h2_tags,  # REAL H2 tags
                "internal_links": internal_links_count,  # REAL count
                "external_links": external_links_count,  # REAL count
                "images": 0,  # Will be updated after images are saved
                "scripts": 0,  # TODO: Extract from HTML
                "stylesheets": 0,  # TODO: Extract from HTML
                "seo_score": self._calculate_seo_score_from_metadata(seo_metadata) if seo_metadata else 0,
                "issues": {}  # Issues are saved to separate table
            }

            # Insert page (removed full_content - doesn't exist in schema)
            result = self.db.table("pages").insert(page_data).execute()
            if hasattr(result, "error") and result.error:
                logger.error(f"Error saving page to database: {result.error}")
            else:
                logger.info(f"Saved page {page.url} to database with title: {title[:50]}")

            # Save SEO metadata to separate table if available
            if seo_metadata:
                await self._save_seo_metadata_to_db(seo_metadata)

        except Exception as e:
            logger.error(f"Error saving page to database: {e}", exc_info=True)

    def _calculate_seo_score_from_metadata(self, seo_metadata: SEOMetadata) -> int:
        """Calculate a basic SEO score from metadata."""
        score = 100

        # Title issues
        if not seo_metadata.title:
            score -= 20
        elif seo_metadata.title_length > 60:
            score -= 10
        elif seo_metadata.title_length < 30:
            score -= 5

        # Meta description issues
        if not seo_metadata.meta_description:
            score -= 15
        elif seo_metadata.meta_description_length > 160:
            score -= 5
        elif seo_metadata.meta_description_length < 120:
            score -= 5

        # H1 issues
        if not seo_metadata.h1:
            score -= 15

        # Image alt text issues
        if seo_metadata.image_alt_missing_count > 0:
            score -= min(20, seo_metadata.image_alt_missing_count * 2)

        return max(0, score)

    async def _save_seo_metadata_to_db(self, seo_metadata: SEOMetadata) -> None:
        """Save SEO metadata to the seo_metadata table."""
        try:
            seo_data = {
                "id": str(uuid4()),
                "page_id": str(seo_metadata.page_id),
                "title": seo_metadata.title,
                "title_length": seo_metadata.title_length,
                "meta_description": seo_metadata.meta_description,
                "meta_description_length": seo_metadata.meta_description_length,
                "h1": seo_metadata.h1,
                "h2": seo_metadata.h2,
                "robots_meta": seo_metadata.robots_meta,
                "hreflang": seo_metadata.hreflang,
                "canonical": seo_metadata.canonical,
                "og_tags": seo_metadata.og_tags,
                "twitter_tags": seo_metadata.twitter_tags,
                "json_ld": seo_metadata.json_ld,
                "image_alt_missing_count": seo_metadata.image_alt_missing_count,
                "internal_links": seo_metadata.internal_links,
                "external_links": seo_metadata.external_links,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            result = self.db.table("seo_metadata").insert(seo_data).execute()
            if hasattr(result, "error") and result.error:
                logger.error(f"Error saving SEO metadata: {result.error}")
            else:
                logger.debug(f"Saved SEO metadata for page {seo_metadata.page_id}")

        except Exception as e:
            logger.error(f"Error saving SEO metadata: {e}", exc_info=True)
    
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
        last_existence_check = time.time()
        
        while self.url_queue and self.pages_crawled < self.crawl.max_pages:
            # Check if max runtime exceeded
            elapsed_time = time.time() - self.start_time
            if elapsed_time > self.crawl.max_runtime_sec:
                logger.warning(f"Max runtime exceeded ({elapsed_time:.0f}s > {self.crawl.max_runtime_sec}s), stopping crawl")
                break
            
            # Periodically check if crawl still exists (every 30 seconds)
            if time.time() - last_existence_check > 30:
                if not await self._verify_crawl_exists():
                    logger.warning(f"Crawl {self.crawl.id} was deleted. Stopping gracefully.")
                    self.crawl_deleted = True
                    break
                last_existence_check = time.time()
            
            # Log progress every 10 pages
            if self.pages_crawled > 0 and self.pages_crawled % 10 == 0:
                logger.info(f"Progress: {self.pages_crawled} pages crawled, {len(self.url_queue)} URLs in queue, {elapsed_time:.0f}s elapsed")
            
            # Get the next URL from the queue
            url, depth, source_url = self.url_queue.pop(0)
            
            # Skip if already visited
            normalized_url = self._normalize_url(url)
            if normalized_url in self.visited_urls:
                continue
            
            self.visited_urls.add(normalized_url)
            
            # Crawl the URL
            try:
                result = await self._crawl_url(url, depth, source_url)
                if result and len(result) == 4:
                    page, seo_metadata, soup, status_code = result

                    # CRITICAL: Save page to database FIRST
                    await self._save_page_to_db(page, seo_metadata)

                    # THEN save images and links (now page exists in DB for foreign key)
                    if status_code == 200:
                        await self._extract_and_process_links(soup, url, depth, page.id)
                        images_count = await self._extract_and_save_images(soup, url, page.id)

                        # Update page with actual image count
                        if images_count > 0:
                            self.db.table("pages").update({"images": images_count}).eq("id", str(page.id)).execute()

                    # Only increment counter if page was successfully saved
                    self.pages_crawled += 1
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                # Don't increment pages_crawled for failed pages
    
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
            
            # Extract text content
            soup = BeautifulSoup(html_content, 'lxml')
            full_text = extracted_data['content']['text'] if extracted_data['content']['text'] else self._extract_text_excerpt(soup)
            # Increase excerpt to 5000 characters for better content preview
            text_excerpt = full_text[:5000] if full_text else ""
            word_count = extracted_data['content']['word_count']

            # Create page record (removed fields not in DB schema: full_content, html_storage_path)
            page = Page(
                crawl_id=self.crawl.id,
                url=url,
                final_url=final_url,
                status_code=status_code,
                method=method,
                render_ms=render_time,
                content_hash=content_hash,
                text_excerpt=text_excerpt,
                word_count=word_count,
                content_type=content_type,
                page_size_bytes=len(html_content)
            )
            
            # Use SmartContentExtractor for comprehensive SEO analysis
            seo_metadata = self._create_enhanced_seo_metadata(extracted_data, page.id)
            
            # Save comprehensive audit data
            await self._save_audit_data(page.id, extracted_data)
            
            # Return the page, metadata, and soup for later processing
            # DO NOT save images/links here - page must be saved to DB first!
            return page, seo_metadata, soup, status_code
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}", exc_info=True)

            # Create a page record for the failed crawl (removed fields not in DB schema)
            page = Page(
                crawl_id=self.crawl.id,
                url=url,
                final_url=url,
                status_code=0,  # 0 indicates error
                method=method,
                render_ms=int((time.time() - start_time) * 1000),
                content_hash=None,
                text_excerpt=f"Error: {str(e)[:500]}",  # Limit error message length
                word_count=0,
                content_type=None,
                page_size_bytes=0
            )

            # Save the error page to database so user can see what failed
            try:
                page_data = {
                    "id": str(page.id),
                    "crawl_id": str(page.crawl_id),
                    "url": page.url,
                    "title": f"Error crawling {url[:50]}",
                    "meta_description": None,
                    "content_summary": f"Failed to crawl: {str(e)[:200]}",
                    "status_code": 0,
                    "response_time": page.render_ms,
                    "content_type": "error",
                    "content_length": 0,
                    "h1_tags": [],
                    "h2_tags": [],
                    "internal_links": 0,
                    "external_links": 0,
                    "images": 0,
                    "scripts": 0,
                    "stylesheets": 0,
                    "seo_score": 0,
                    "issues": {"crawl_error": str(e)[:500]}
                }

                result = self.db.table("pages").insert(page_data).execute()
                if hasattr(result, "error") and result.error:
                    logger.error(f"Error saving failed page to database: {result.error}")
                else:
                    logger.info(f"Saved error page for {url} to database")

                # Also save to issues table for visibility
                issue_data = {
                    "id": str(uuid4()),
                    "crawl_id": str(self.crawl.id),
                    "page_id": str(page.id),
                    "type": "Crawl Error",
                    "severity": "high",
                    "message": f"Failed to crawl URL: {str(e)[:500]}",
                    "pointer": None,
                    "context": url,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                result = self.db.table("issues").insert(issue_data).execute()
                if hasattr(result, "error") and result.error:
                    logger.error(f"Error saving issue to database: {result.error}")

            except Exception as save_error:
                logger.error(f"Error saving failed page data: {save_error}")

            return None  # Return None to indicate failure (don't increment pages_crawled)
    
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
                "is_nofollow": bool(link.get('rel') and 'nofollow' in link.get('rel', [])),  # Ensure boolean
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
            result = self.db.table("links").insert(link_data).execute()
            if hasattr(result, "error") and result.error:
                error_msg = str(result.error)
                # Check for foreign key violation (crawl was deleted)
                if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                    logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping link save.")
                    self.crawl_deleted = True
                    return
                logger.error(f"Error saving link: {result.error}")
            else:
                logger.debug(f"Saved link {link_data['target_url'][:100]}")
        except Exception as e:
            error_msg = str(e)
            # Check for foreign key violation (crawl was deleted)
            if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping link save.")
                self.crawl_deleted = True
                return
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

    async def _extract_and_save_images(
        self,
        soup: BeautifulSoup,
        page_url: str,
        page_id: str
    ) -> int:
        """Extract images from page and save to database. Returns count of images saved."""
        saved_count = 0
        try:
            # Check if crawl still exists before processing images
            if self.crawl_deleted:
                logger.info(f"Crawl was deleted. Skipping image extraction.")
                return 0
            
            images = soup.find_all('img')
            logger.info(f"Found {len(images)} images on {page_url}")

            for img in images:
                # Stop if crawl was deleted
                if self.crawl_deleted:
                    logger.info(f"Crawl was deleted during image processing. Stopping.")
                    break
                src = img.get('src')
                if not src:
                    continue

                # Resolve relative URLs
                absolute_src = urljoin(page_url, src)

                # Get image metadata
                alt_text = img.get('alt')
                title_text = img.get('title')
                width = img.get('width')
                height = img.get('height')

                # Convert width/height to integers if they exist
                try:
                    width = int(width) if width and str(width).isdigit() else None
                    height = int(height) if height and str(height).isdigit() else None
                except (ValueError, TypeError):
                    width = None
                    height = None

                image_data = {
                    "id": str(uuid4()),
                    "crawl_id": str(self.crawl.id),
                    "page_id": str(page_id),
                    "src": absolute_src,
                    "alt": alt_text[:500] if alt_text else None,  # Limit length
                    "title": title_text[:500] if title_text else None,
                    "width": width,
                    "height": height,
                    "has_alt": bool(alt_text and alt_text.strip()),
                    "is_broken": False,  # Will be checked later if needed
                    "status_code": None,
                    "error": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                # Save to database
                success = await self._save_image(image_data)
                if success:
                    saved_count += 1

            logger.info(f"Saved {saved_count}/{len(images)} images for {page_url}")
            return saved_count

        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return saved_count

    async def _save_image(self, image_data: Dict) -> bool:
        """Save image to database. Returns True if successful."""
        try:
            result = self.db.table("images").insert(image_data).execute()
            if hasattr(result, "error") and result.error:
                error_msg = str(result.error)
                # Check for foreign key violation (crawl was deleted)
                if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                    logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping image save.")
                    self.crawl_deleted = True
                    return False
                logger.error(f"Error saving image: {result.error}")
                return False
            else:
                logger.debug(f"Saved image {image_data['src'][:100]}")
                return True
        except Exception as e:
            error_msg = str(e)
            # Check for foreign key violation (crawl was deleted)
            if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping image save.")
                self.crawl_deleted = True
                return False
            logger.error(f"Error saving image: {e}")
            return False

    async def _verify_crawl_exists(self) -> bool:
        """Verify that the crawl still exists in the database."""
        try:
            result = self.db.table("crawls").select("id").eq("id", str(self.crawl.id)).execute()
            exists = result.data and len(result.data) > 0
            if not exists:
                self.crawl_deleted = True
            return exists
        except Exception as e:
            logger.error(f"Error verifying crawl existence: {e}")
            # Assume it exists if we can't verify (avoid false positives)
            return True

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
            # NOTE: seo_audits table doesn't exist in schema - removed
            # Keeping only issues table insert which does exist

            # Save individual issues for detailed reporting
            issues = self._generate_issues_list(page_id, extracted_data)
            if issues:
                result = self.db.table("issues").insert(issues).execute()
                if hasattr(result, "error") and result.error:
                    logger.error(f"Error saving issues: {result.error}")
                else:
                    logger.debug(f"Saved {len(issues)} issues for page {page_id}")
                    
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
                'page_id': str(page_id),  # Convert UUID to string
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
            
            result = self.db.table("crawls").update(update_data).eq("id", str(self.crawl.id)).execute()
            
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
