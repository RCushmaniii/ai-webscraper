import asyncio
import hashlib
import httpx
import logging
import time
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urljoin, urlparse, unquote

from playwright.async_api import async_playwright

from app.models.models import Crawl, Page, SEOMetadata, CrawlProgress, Link, Issue
from uuid import uuid4
from app.db.supabase import supabase_client
from app.core.config import settings
from app.services.storage import store_html_snapshot
from app.services.content_extractor import SmartContentExtractor
from app.core.domain_blacklist import is_domain_blacklisted, get_blacklist_reason
from app.services.nav_detector import NavDetector

logger = logging.getLogger(__name__)

class Crawler:
    """
    Crawler service responsible for crawling websites and extracting data.
    Follows Single Responsibility Principle by focusing only on crawling logic.
    """

    def __init__(self, crawl: Crawl, db_client=None):
        self.crawl = crawl
        self.visited_urls: Set[str] = set()
        self.url_queue: List[Tuple[str, int, Optional[str], int, bool]] = []  # (url, depth, source_url, nav_score, is_navigation)
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
        # Track external domains to enforce max_external_links limit
        self.external_domains_crawled: Set[str] = set()
        # Navigation detection - stores nav scores for priority crawling
        self.nav_scores: Dict[str, int] = {}  # URL -> navigation score
        self.primary_nav_urls: Set[str] = set()  # High-priority navigation URLs
        self.nav_detection_done = False
        
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

        # ALWAYS run navigation detection on the homepage first
        # This ensures we detect main nav links even if crawl starts from a subpage
        await self._detect_navigation_from_homepage()

        # Check if starting URL is the homepage
        parsed_start = urlparse(self.crawl.url)
        is_homepage = parsed_start.path in ('', '/', '') and not parsed_start.query

        # Determine nav_score for starting URL using full calculation (includes depth bonus)
        # BUG FIX: Previously only used nav_scores.get() which missed depth bonus
        start_nav_score = self._calculate_nav_score(self.crawl.url, 0)  # Depth 0 = starting page

        # Starting URL is ALWAYS a main page (it's what the user wants to crawl!)
        # Also consider it main if: in primary nav, high score, or is homepage
        start_is_nav = True  # Starting URL is always primary

        # Initialize the queue with the start URL (starting pages get max nav_score)
        self.url_queue.append((self.crawl.url, 0, None, max(start_nav_score, 10), start_is_nav))

        # Process robots.txt and sitemaps if policy allows
        if self.crawl.respect_robots_txt:
            await self._process_robots_and_sitemaps()

        # Start crawling
        await self._crawl()

        # Post-crawl analysis: Apply small-site mode if needed
        if not self.crawl_deleted:
            await self._apply_small_site_mode()

        # Close the HTTP client
        await self.client.aclose()

        if self.crawl_deleted:
            logger.info(f"Crawl {self.crawl.id} was deleted during processing. Stopped gracefully.")
        else:
            logger.info(f"Crawl completed for {self.crawl.url}")

    async def _detect_navigation_from_homepage(self) -> None:
        """
        Always detect navigation links from the homepage.
        This runs regardless of what URL the crawl starts from, ensuring
        we identify main navigation links for priority crawling.
        """
        try:
            # Construct homepage URL from the domain
            parsed = urlparse(self.crawl.url)
            homepage_url = f"{parsed.scheme}://{parsed.netloc}/"

            logger.info(f"Running navigation detection on homepage: {homepage_url}")

            # Fetch the homepage
            await self.rate_limiter.wait()
            response = await self.client.get(homepage_url)

            if response.status_code != 200:
                logger.warning(f"Homepage returned status {response.status_code}, skipping nav detection")
                self.nav_detection_done = True
                return

            html_content = response.text

            # Run NavDetector on homepage
            detector = NavDetector(html_content, homepage_url)
            nav_data = detector.extract_nav_links()

            # Store navigation scores for prioritization
            for link_info in nav_data.get('all_detected', []):
                self.nav_scores[link_info['url']] = link_info['score']

            # Store primary nav URLs for high-priority crawling
            self.primary_nav_urls = set(nav_data.get('primary_nav', []))

            logger.info(
                f"Navigation detection complete: {len(self.primary_nav_urls)} primary nav links, "
                f"{nav_data.get('total_nav_links', 0)} total nav links detected"
            )

            # Log the primary nav URLs for debugging
            if self.primary_nav_urls:
                logger.info(f"Primary navigation URLs: {list(self.primary_nav_urls)[:10]}")

            self.nav_detection_done = True

        except Exception as e:
            logger.warning(f"Navigation detection from homepage failed: {e}")
            self.nav_detection_done = True

    async def _finalize_primary_pages(self) -> None:
        """
        Post-crawl finalization: Mark ONLY true main pages as primary.

        STRICT STRATEGY (aim for 8-15 main pages max):
        1. Homepage is ALWAYS a main page
        2. Only pages linked from PRIMARY navigation (nav_score >= 8)
        3. Apply strict URL exclusions (blog posts, categories, paginated content)
        4. Hard cap of 15 main pages maximum
        5. For very small sites (≤6 pages), all non-excluded pages are main

        This is intentionally restrictive - main pages are for client reports.
        """
        import re

        MAX_MAIN_PAGES = 15  # Hard cap - never exceed this
        MIN_NAV_SCORE = 8   # Only high-confidence nav links

        try:
            # Get all pages for this crawl with their nav_scores
            pages_result = self.db.table("pages").select("id, url, nav_score, is_primary, depth").eq("crawl_id", str(self.crawl.id)).execute()

            if not pages_result.data:
                return

            total_pages = len(pages_result.data)
            logger.info(f"Finalizing primary pages for crawl {self.crawl.id} ({total_pages} pages)")

            # STRICT exclusion patterns - these are NEVER main pages
            exclude_patterns = [
                # Legal/utility pages
                r'/privacy', r'/terms', r'/legal', r'/cookie', r'/gdpr',
                r'/imprint', r'/disclaimer', r'/login', r'/signin', r'/signup',
                r'/register', r'/cart', r'/checkout', r'/account', r'/404', r'/error',
                # Blog/news content (individual posts, not index)
                r'/blog/.+', r'/news/.+', r'/article/', r'/post/',
                r'/\d{4}/\d{2}/',  # Date-based URLs like /2024/01/post-title
                # Categories, tags, archives
                r'/category/', r'/tag/', r'/tags/', r'/author/', r'/archive/',
                # Pagination
                r'/page/\d+', r'\?page=', r'\?p=',
                # Search results
                r'/search', r'\?q=', r'\?s=',
                # Media/files
                r'/wp-content/', r'/uploads/', r'/media/', r'/assets/',
                # Language/locale specific subpaths (but allow /en/, /es/ at root)
                r'/[a-z]{2}/[a-z]+/.+',  # Like /en/blog/post - exclude deep content
            ]

            # First, reset ALL pages to is_primary=False (clean slate)
            # Then selectively mark the true main pages

            # Identify main page candidates
            main_page_candidates = []

            parsed_start = urlparse(self.crawl.url)
            start_domain = parsed_start.netloc

            for page in pages_result.data:
                url = page.get('url', '')
                parsed = urlparse(url)
                path = parsed.path.lower()
                nav_score = page.get('nav_score', 0)
                depth = page.get('depth', 99)

                # Skip if different domain (external links)
                if parsed.netloc != start_domain:
                    continue

                # Check exclusion patterns - if ANY match, skip this page
                is_excluded = any(re.search(pattern, path) for pattern in exclude_patterns)
                if is_excluded:
                    continue

                # Check exclusion patterns in query string too
                if parsed.query and any(re.search(pattern, '?' + parsed.query) for pattern in exclude_patterns):
                    continue

                # CRITERIA FOR MAIN PAGE:
                is_homepage = path in ('', '/', '') and not parsed.query
                is_high_nav_score = nav_score >= MIN_NAV_SCORE
                is_very_small_site = total_pages <= 6

                # Only consider as main page if:
                # 1. It's the homepage, OR
                # 2. It has high nav_score (linked from primary nav), OR
                # 3. Site is very small (≤6 pages)
                if is_homepage or is_high_nav_score or is_very_small_site:
                    main_page_candidates.append({
                        'id': page['id'],
                        'url': url,
                        'nav_score': nav_score,
                        'depth': depth,
                        'is_homepage': is_homepage
                    })

            # Sort candidates: homepage first, then by nav_score (desc), then by URL depth (asc)
            # NOTE: Using URL slash count instead of crawl depth for tiebreaker
            # Reason: In Mega Menus, ALL links have crawl_depth=1 (all on homepage)
            # URL slash count correctly identifies /services as parent of /services/consulting/finance
            main_page_candidates.sort(key=lambda x: (
                not x['is_homepage'],  # Homepage first (False sorts before True)
                -x['nav_score'],       # Higher scores first
                x['url'].count('/')    # Shorter URLs first (structural hierarchy)
            ))

            # Apply hard cap
            final_main_pages = main_page_candidates[:MAX_MAIN_PAGES]
            main_page_ids = {p['id'] for p in final_main_pages}

            logger.info(f"Selected {len(final_main_pages)} main pages from {len(main_page_candidates)} candidates (cap: {MAX_MAIN_PAGES})")

            # Update database: mark selected pages as primary, others as not primary
            updates_made = 0
            for page in pages_result.data:
                should_be_primary = page['id'] in main_page_ids
                currently_primary = page.get('is_primary', False)

                # Only update if state needs to change
                if should_be_primary != currently_primary:
                    try:
                        self.db.table("pages").update({
                            'is_primary': should_be_primary
                        }).eq('id', page['id']).execute()
                        updates_made += 1
                    except Exception as e:
                        logger.warning(f"Failed to update page {page['id']}: {e}")

            logger.info(f"Primary page finalization complete: {len(final_main_pages)} main pages, {updates_made} updates made")

            # Log the selected main pages for debugging
            if final_main_pages:
                main_urls = [p['url'] for p in final_main_pages[:10]]  # Log first 10
                logger.info(f"Main pages selected: {main_urls}")

        except Exception as e:
            logger.warning(f"Primary page finalization failed: {e}")

    # Keep old name as alias for backwards compatibility
    async def _apply_small_site_mode(self) -> None:
        """Alias for _finalize_primary_pages for backwards compatibility."""
        await self._finalize_primary_pages()

    async def _save_page_to_db(self, page: Page, seo_metadata: Optional[SEOMetadata], nav_score: int = 0, is_navigation: bool = False, depth: int = 0) -> None:
        """Save page and SEO metadata to database.

        Args:
            page: The page object to save
            seo_metadata: Optional SEO metadata for the page
            nav_score: Navigation importance score (0-20+) from link that led here
            is_navigation: True if this page was linked from main navigation
            depth: Crawl depth (0 = starting URL, 1 = directly linked, etc.)
        """
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
                "html_snapshot_path": page.html_storage_path,  # Path to full HTML for content retrieval
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
                "issues": {},  # Issues are saved to separate table
                "nav_score": nav_score,  # Navigation importance score from link
                "is_primary": False,  # Set by _finalize_primary_pages at end of crawl
                "depth": depth  # Crawl depth (0 = starting, 1 = linked from start, etc.)
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

    def _calculate_nav_score(self, url: str, depth: int) -> int:
        """
        Calculate comprehensive navigation score for a URL.

        Combines:
        - NavDetector scores (from homepage analysis)
        - Depth scoring (shallow = more important)
        - URL pattern scoring (bonus for main pages, penalty for blog/legal)

        Args:
            url: The URL to score
            depth: The crawl depth of this URL

        Returns:
            Navigation score (0-30+, higher = more likely main page)
        """
        import re

        # Start with NavDetector score (if any)
        score = self.nav_scores.get(url, 0)

        # DEPTH SCORING - shallow URLs are more likely to be main pages
        # Depth 0 (homepage): +10
        # Depth 1 (directly linked from homepage): +8
        # Depth 2: +4
        # Depth 3+: +0
        depth_bonuses = {0: 10, 1: 8, 2: 4}
        score += depth_bonuses.get(depth, 0)

        # URL PATTERN SCORING
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Bonus patterns - likely main pages (+5 each)
        main_page_patterns = [
            r'^/$',                      # Homepage
            r'^/about',                  # About pages
            r'^/contact',                # Contact
            r'^/services',               # Services
            r'^/products',               # Products
            r'^/pricing',                # Pricing
            r'^/features',               # Features
            r'^/solutions',              # Solutions
            r'^/team',                   # Team
            r'^/careers?',               # Careers
            r'^/case-stud',              # Case studies
            r'^/portfolio',              # Portfolio
            r'^/work$',                  # Work/Projects
            r'^/clients',                # Clients
            r'^/testimonials',           # Testimonials
            r'^/faq',                    # FAQ
            r'^/blog$',                  # Blog index (not posts)
            r'^/news$',                  # News index
        ]

        for pattern in main_page_patterns:
            if re.match(pattern, path):
                score += 5
                break

        # Penalty patterns - likely NOT main pages (-10 each)
        penalty_patterns = [
            r'/blog/.+',                 # Blog posts (not index)
            r'/news/.+',                 # News articles
            r'/posts?/',                 # Posts
            r'/articles?/',              # Articles
            r'/\d{4}/\d{2}/',            # Date-based URLs
            r'/tag/',                    # Tag pages
            r'/tags/',
            r'/category/',               # Category pages
            r'/author/',                 # Author pages
            r'/page/\d+',                # Pagination
            r'\?',                       # Query strings
        ]

        for pattern in penalty_patterns:
            if re.search(pattern, path):
                score -= 10
                break

        # Legal/utility penalty (-15) - these are rarely "main" pages
        utility_patterns = [
            r'/privacy',
            r'/terms',
            r'/legal',
            r'/cookie',
            r'/gdpr',
            r'/imprint',
            r'/disclaimer',
            r'/login',
            r'/signin',
            r'/signup',
            r'/register',
            r'/cart',
            r'/checkout',
            r'/account',
        ]

        for pattern in utility_patterns:
            if re.search(pattern, path):
                score -= 15
                break

        return max(0, score)  # Don't go negative

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
                                # Use 5-tuple format: (url, depth, source_url, nav_score, is_navigation)
                                self.url_queue.append((url, 0, None, 0, False))
        
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
            queue_item = self.url_queue.pop(0)
            # Handle both old format (3-tuple) and new format (5-tuple)
            if len(queue_item) == 5:
                url, depth, source_url, nav_score, is_navigation = queue_item
            else:
                url, depth, source_url = queue_item
                nav_score, is_navigation = 0, False

            # Skip if already visited
            normalized_url = self._normalize_url(url)
            if normalized_url in self.visited_urls:
                continue

            self.visited_urls.add(normalized_url)

            # Crawl the URL
            try:
                result = await self._crawl_url(url, depth, source_url)
                if result and len(result) == 5:
                    page, seo_metadata, soup, extracted_data, status_code = result

                    # CRITICAL: Save page to database FIRST (include navigation info + depth)
                    await self._save_page_to_db(page, seo_metadata, nav_score, is_navigation, depth)

                    # THEN save audit data (now page exists in DB for foreign key)
                    if extracted_data:
                        await self._save_audit_data(page.id, extracted_data)

                    # THEN save images and links (now page exists in DB for foreign key)
                    # Only extract links/images for HTML pages (soup will be None for PDFs, images, etc.)
                    if status_code == 200 and soup is not None:
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

            # Skip non-HTML content types (PDFs, images, etc.) - don't try to parse them
            if "text/html" not in content_type.lower():
                render_time = int((time.time() - start_time) * 1000)

                # Extract filename from URL for a meaningful title
                parsed = urlparse(url)
                filename = unquote(parsed.path.split('/')[-1]) or url
                resource_type = content_type.split(';')[0].strip() if content_type else "Unknown"

                # Create a basic page record for non-HTML resources
                page = Page(
                    crawl_id=self.crawl.id,
                    url=url,
                    final_url=final_url,
                    status_code=status_code,
                    method="http",
                    render_ms=render_time,
                    content_hash=None,
                    text_excerpt=f"Non-HTML resource: {resource_type}",
                    word_count=0,
                    content_type=content_type,
                    page_size_bytes=int(response.headers.get("content-length", 0))
                )

                # Create minimal SEO metadata with filename as title
                seo_metadata = SEOMetadata(
                    page_id=page.id,
                    title=f"{filename} ({resource_type})",
                    title_length=len(filename),
                    meta_description=f"Non-HTML resource: {resource_type}",
                    meta_description_length=0,
                    h1=None,
                    h2=[],
                    canonical=None,
                    robots_meta=None,
                    og_tags=None,
                    twitter_tags=None,
                    json_ld=None,
                    hreflang=None,
                    internal_links=0,
                    external_links=0,
                    image_alt_missing_count=0
                )

                # Return consistent 5-item tuple
                logger.info(f"Skipping non-HTML content ({resource_type}): {url}")
                return page, seo_metadata, None, None, status_code

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
            
            # Extract text content - use full page text for marketing pages
            soup = BeautifulSoup(html_content, 'lxml')
            # Prefer full_page_text (all visible content) over article-focused extraction
            full_text = extracted_data['content'].get('full_page_text') or extracted_data['content']['text'] or self._extract_text_excerpt(soup)
            # Store up to 50,000 characters (~7,500 words) to capture full marketing page copy
            # This ensures hero sections, features, testimonials, CTAs are all captured
            text_excerpt = full_text[:50000] if full_text else ""
            word_count = extracted_data['content']['word_count']

            # Create page record with HTML snapshot path for full content retrieval
            page = Page(
                crawl_id=self.crawl.id,
                url=url,
                final_url=final_url,
                status_code=status_code,
                method=method,
                render_ms=render_time,
                content_hash=content_hash,
                html_storage_path=html_storage_path,  # Path to stored HTML file
                text_excerpt=text_excerpt,
                word_count=word_count,
                content_type=content_type,
                page_size_bytes=len(html_content)
            )
            
            # Use SmartContentExtractor for comprehensive SEO analysis
            seo_metadata = self._create_enhanced_seo_metadata(extracted_data, page.id)
            
            # Return the page, metadata, soup, extracted_data, and status_code for later processing
            # DO NOT save audit/images/links here - page must be saved to DB first!
            return page, seo_metadata, soup, extracted_data, status_code
            
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

            # Return None to indicate failure (main loop will skip this page)
            return None
    
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
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait for JS to execute and render dynamic content
                await asyncio.sleep(3)
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
        # Run navigation detection on the first page (homepage) to identify priority links
        if not self.nav_detection_done and depth == 0:
            try:
                html_content = str(soup)
                detector = NavDetector(html_content, source_url)
                nav_data = detector.extract_nav_links()

                # Store navigation scores for prioritization
                for link_info in nav_data.get('all_detected', []):
                    self.nav_scores[link_info['url']] = link_info['score']

                # Store primary nav URLs for high-priority crawling
                self.primary_nav_urls = set(nav_data.get('primary_nav', []))

                logger.info(f"Navigation detection complete: {len(self.primary_nav_urls)} primary nav links, "
                           f"{nav_data.get('total_nav_links', 0)} total nav links detected")
                self.nav_detection_done = True
            except Exception as e:
                logger.warning(f"Navigation detection failed: {e}")
                self.nav_detection_done = True

        links = soup.find_all('a', href=True)

        # PERFORMANCE: Batch collect all links before saving
        links_to_save = []
        links_to_check = []
        nav_links_to_queue = []  # Priority queue for navigation links

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
            elif not is_internal and self.crawl.follow_external_links and new_depth <= self.crawl.external_depth:
                # EXTERNAL LINK SAFETY CHECKS

                # Check 1: Is domain blacklisted?
                if is_domain_blacklisted(absolute_url):
                    reason = get_blacklist_reason(absolute_url)
                    logger.debug(f"Skipping blacklisted domain: {parsed_url.netloc} (reason: {reason})")
                    should_follow = False
                # Check 2: Have we reached max external domains limit?
                elif parsed_url.netloc not in self.external_domains_crawled and len(self.external_domains_crawled) >= self.crawl.max_external_links:
                    logger.debug(f"Max external domains reached ({self.crawl.max_external_links}). Skipping: {parsed_url.netloc}")
                    should_follow = False
                else:
                    # Safe to follow - track this external domain
                    self.external_domains_crawled.add(parsed_url.netloc)
                    should_follow = True
                    logger.info(f"Following external link to: {parsed_url.netloc} (external domains: {len(self.external_domains_crawled)}/{self.crawl.max_external_links})")

            # Calculate comprehensive navigation score for this URL
            nav_score = self._calculate_nav_score(absolute_url, new_depth)
            is_navigation = absolute_url in self.primary_nav_urls or nav_score >= 8

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
                "nav_score": nav_score,  # Navigation importance score
                "is_navigation": is_navigation,  # Is this a main navigation link?
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Handle link based on whether we'll crawl it
            if should_follow:
                # Prioritize navigation links in the queue
                # CRITICAL: Include nav_score and is_navigation in the 5-tuple!
                if is_navigation and is_internal:
                    # Navigation links go to front of queue
                    nav_links_to_queue.append((absolute_url, new_depth, source_url, nav_score, is_navigation))
                else:
                    # Regular links go to back of queue
                    self.url_queue.append((absolute_url, new_depth, source_url, nav_score, is_navigation))
                # Collect for batch save
                links_to_save.append(link_data)
            else:
                # For links we won't crawl, decide if we need status check
                if is_internal:
                    # Check status for internal links we're not crawling
                    links_to_check.append(link_data)
                else:
                    # Skip status check for external links to speed up crawl
                    links_to_save.append(link_data)

        # Insert navigation links at the FRONT of the queue for priority crawling
        if nav_links_to_queue:
            logger.info(f"Prioritizing {len(nav_links_to_queue)} navigation links in crawl queue")
            self.url_queue = nav_links_to_queue + self.url_queue

        # PERFORMANCE: Batch save all links in ONE database call
        if links_to_save:
            await self._save_links_batch(links_to_save)

        # Check status for internal links that need it (done individually due to HTTP requests)
        if links_to_check:
            for link_data in links_to_check:
                await self._check_and_save_link(link_data)
    
    async def _save_link(self, link_data: Dict) -> None:
        """Save a single link to the database."""
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

    async def _save_links_batch(self, links_data: List[Dict]) -> None:
        """
        PERFORMANCE: Save multiple links in ONE database call.
        This is 10-50x faster than individual inserts.
        """
        try:
            result = self.db.table("links").insert(links_data).execute()
            if hasattr(result, "error") and result.error:
                error_msg = str(result.error)
                # Check for foreign key violation (crawl was deleted)
                if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                    logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping batch link save.")
                    self.crawl_deleted = True
                    return
                logger.error(f"Error batch saving links: {result.error}")
            else:
                logger.info(f"Batch saved {len(links_data)} links in one database call")
        except Exception as e:
            error_msg = str(e)
            # Check for foreign key violation (crawl was deleted)
            if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping batch link save.")
                self.crawl_deleted = True
                return
            logger.error(f"Error batch saving links: {e}")

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
        try:
            # Check if crawl still exists before processing images
            if self.crawl_deleted:
                logger.info(f"Crawl was deleted. Skipping image extraction.")
                return 0

            images = soup.find_all('img')

            if not images:
                return 0

            logger.debug(f"Found {len(images)} images on {page_url}")

            # PERFORMANCE: Batch collect all images before saving
            images_to_save = []

            for img in images:
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

                images_to_save.append(image_data)

            # PERFORMANCE: Batch save all images in ONE database call
            if images_to_save:
                success = await self._save_images_batch(images_to_save)
                if success:
                    logger.info(f"Batch saved {len(images_to_save)} images for {page_url}")
                    return len(images_to_save)

            return 0

        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return 0

    async def _save_image(self, image_data: Dict) -> bool:
        """Save a single image to database. Returns True if successful."""
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

    async def _save_images_batch(self, images_data: List[Dict]) -> bool:
        """
        PERFORMANCE: Save multiple images in ONE database call.
        This is 10-50x faster than individual inserts.
        """
        try:
            result = self.db.table("images").insert(images_data).execute()
            if hasattr(result, "error") and result.error:
                error_msg = str(result.error)
                # Check for foreign key violation (crawl was deleted)
                if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                    logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping batch image save.")
                    self.crawl_deleted = True
                    return False
                logger.error(f"Error batch saving images: {result.error}")
                return False
            else:
                logger.info(f"Batch saved {len(images_data)} images in one database call")
                return True
        except Exception as e:
            error_msg = str(e)
            # Check for foreign key violation (crawl was deleted)
            if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                logger.warning(f"Crawl {self.crawl.id} was deleted. Skipping batch image save.")
                self.crawl_deleted = True
                return False
            logger.error(f"Error batch saving images: {e}")
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
        """Generate comprehensive list of actionable issues (Phase 1: Using existing data)."""
        issues = []
        url = extracted_data.get('url', '')
        
        # 1. PERFORMANCE ISSUES
        
        # Large page size (> 3MB)
        page_size_bytes = extracted_data.get('technical', {}).get('page_size_bytes', 0)
        if page_size_bytes > 3 * 1024 * 1024:  # 3MB
            page_size_mb = page_size_bytes / (1024 * 1024)
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'Performance',
                'severity': 'high',
                'message': f'Large page size: {page_size_mb:.1f}MB (recommended < 3MB)',
                'pointer': 'page_size',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # 2. ACCESSIBILITY ISSUES
        
        # Images missing alt text
        images = extracted_data.get('images', [])
        images_without_alt = [img for img in images if not img.get('has_alt')]
        if images_without_alt:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'Accessibility',
                'severity': 'high',
                'message': f'{len(images_without_alt)} image(s) missing alt text (accessibility & SEO issue)',
                'pointer': 'images',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # Missing viewport meta tag
        if not extracted_data.get('technical', {}).get('has_viewport_meta'):
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'Accessibility',
                'severity': 'critical',
                'message': 'Missing viewport meta tag (mobile responsiveness issue)',
                'pointer': 'viewport',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # 3. SEO ISSUES
        
        # Missing title
        seo_data = extracted_data.get('seo', {})
        if not seo_data.get('title'):
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'critical',
                'message': 'Missing title tag (critical SEO issue)',
                'pointer': 'title',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        # Title too short or too long
        elif seo_data.get('title_length', 0) < 30:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'medium',
                'message': f'Title too short: {seo_data.get("title_length")} characters (recommended 30-60)',
                'pointer': 'title',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        elif seo_data.get('title_length', 0) > 60:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'medium',
                'message': f'Title too long: {seo_data.get("title_length")} characters (recommended 30-60)',
                'pointer': 'title',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # Missing meta description
        if not seo_data.get('meta_description'):
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'high',
                'message': 'Missing meta description (impacts click-through rate)',
                'pointer': 'meta_description',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        # Meta description too short or too long
        elif seo_data.get('description_length', 0) < 120:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'medium',
                'message': f'Meta description too short: {seo_data.get("description_length")} characters (recommended 120-160)',
                'pointer': 'meta_description',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        elif seo_data.get('description_length', 0) > 160:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'medium',
                'message': f'Meta description too long: {seo_data.get("description_length")} characters (recommended 120-160)',
                'pointer': 'meta_description',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # 4. CONTENT QUALITY ISSUES
        
        # Thin content (< 300 words)
        word_count = extracted_data.get('content', {}).get('word_count', 0)
        if word_count > 0 and word_count < 300:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'Content Quality',
                'severity': 'medium',
                'message': f'Thin content: {word_count} words (recommended 500+ for key pages)',
                'pointer': 'word_count',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # Missing H1
        headings = extracted_data.get('content', {}).get('headings', [])
        h1_count = len([h for h in headings if h.get('level') == 1])
        if h1_count == 0:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'high',
                'message': 'Missing H1 heading (important for SEO and accessibility)',
                'pointer': 'h1',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        # Multiple H1s
        elif h1_count > 1:
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'SEO',
                'severity': 'medium',
                'message': f'Multiple H1 headings found ({h1_count}). Use only one H1 per page.',
                'pointer': 'h1',
                'context': url,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # Broken heading hierarchy
        prev_level = 0
        for heading in headings:
            level = heading.get('level', 0)
            if level > prev_level + 1 and prev_level > 0:
                issues.append({
                    'id': str(uuid4()),
                    'crawl_id': str(self.crawl.id),
                    'page_id': str(page_id),
                    'type': 'SEO',
                    'severity': 'low',
                    'message': f'Heading hierarchy skip: H{prev_level} to H{level} (should be sequential)',
                    'pointer': 'headings',
                    'context': url,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                break  # Only report first hierarchy issue
            prev_level = level
        
        # 5. TECHNICAL ISSUES
        
        # Missing lang attribute
        if not extracted_data.get('technical', {}).get('has_lang_attribute'):
            issues.append({
                'id': str(uuid4()),
                'crawl_id': str(self.crawl.id),
                'page_id': str(page_id),
                'type': 'Technical',
                'severity': 'medium',
                'message': 'Missing lang attribute on <html> tag (accessibility & SEO)',
                'pointer': 'lang',
                'context': url,
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
