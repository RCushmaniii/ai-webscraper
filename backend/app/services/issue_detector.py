"""
Issue Detection Service - Phase 1 (Quick Wins)

Detects actionable issues using existing crawl data without requiring
additional data collection or AI processing.

Based on ISSUE_DETECTION_SPEC.md Phase 1 requirements.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from collections import Counter
from urllib.parse import urlparse

from app.db.supabase import supabase_client

logger = logging.getLogger(__name__)


def normalize_url_for_comparison(url: str) -> str:
    """
    Normalize a URL for duplicate comparison.
    - Removes www. prefix
    - Removes trailing slashes
    - Lowercases the domain

    This prevents www.example.com/page and example.com/page from being
    counted as duplicates.
    """
    if not url:
        return url

    try:
        parsed = urlparse(url)
        # Normalize domain (remove www., lowercase)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]

        # Normalize path (remove trailing slash unless it's just /)
        path = parsed.path
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # Reconstruct normalized URL (without query/fragment for comparison)
        return f"{parsed.scheme}://{domain}{path}"
    except Exception:
        return url


class IssueDetector:
    """
    Detects issues in crawled data based on best practices and common problems.
    Focuses on Phase 1 detection using existing data only.
    """

    # Content types that should be excluded from HTML-specific checks
    NON_HTML_CONTENT_TYPES = [
        'application/pdf',
        'image/',
        'video/',
        'audio/',
        'application/zip',
        'application/octet-stream',
        'text/plain',
        'text/css',
        'application/javascript',
        'application/json',
        'application/xml',
    ]

    def __init__(self, crawl_id: UUID, db_client=None):
        self.crawl_id = crawl_id
        # Use provided db_client (service role) or fall back to default supabase_client
        # This allows the detector to work in both HTTP request context and Celery background tasks
        self.db = db_client if db_client is not None else supabase_client
        self.issues: List[Dict[str, Any]] = []

    def _is_html_page(self, page: Dict[str, Any]) -> bool:
        """Check if a page is an HTML page (not PDF, image, etc.)."""
        content_type = page.get("content_type", "") or ""
        title = page.get("title", "") or ""
        url = page.get("url", "") or ""

        # Check content type
        for non_html_type in self.NON_HTML_CONTENT_TYPES:
            if non_html_type in content_type.lower():
                return False

        # Check URL extension for common non-HTML files
        url_lower = url.lower()
        non_html_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
                               '.mp4', '.mp3', '.wav', '.zip', '.doc', '.docx', '.xls',
                               '.xlsx', '.ppt', '.pptx', '.csv', '.json', '.xml']
        for ext in non_html_extensions:
            if url_lower.endswith(ext):
                return False

        # Also check title pattern for non-HTML resources (fallback)
        # Our crawler sets titles like "filename.pdf (application/pdf)" for non-HTML
        if '(application/' in title or '(image/' in title:
            return False

        return True

    async def detect_all_issues(self) -> List[Dict[str, Any]]:
        """
        Run all Phase 1 issue detection checks.
        Returns a list of detected issues.
        """
        logger.info(f"Starting Phase 1 issue detection for crawl {self.crawl_id}")

        try:
            # Fetch all necessary data
            pages = await self._fetch_pages()
            links = await self._fetch_links()
            images = await self._fetch_images()
            seo_metadata = await self._fetch_seo_metadata()

            # Run all detection checks
            await self._detect_broken_links(links)
            await self._detect_broken_images(images)
            await self._detect_large_pages(pages)
            await self._detect_large_images(images)
            await self._detect_missing_alt_text(images)
            await self._detect_thin_content(pages)
            await self._detect_orphan_pages(pages, links)
            await self._detect_duplicate_titles(seo_metadata)
            await self._detect_duplicate_descriptions(seo_metadata)
            await self._detect_missing_h1(seo_metadata)
            await self._detect_multiple_h1s(seo_metadata)

            logger.info(f"Detected {len(self.issues)} issues for crawl {self.crawl_id}")
            return self.issues

        except Exception as e:
            logger.error(f"Error detecting issues for crawl {self.crawl_id}: {e}")
            return []

    async def _fetch_pages(self) -> List[Dict[str, Any]]:
        """Fetch all pages for the crawl."""
        try:
            response = self.db.table("pages").select("*").eq("crawl_id", str(self.crawl_id)).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching pages: {e}")
            return []

    async def _fetch_links(self) -> List[Dict[str, Any]]:
        """Fetch all links for the crawl with source page URLs."""
        try:
            # Join with pages table to get source page URLs
            response = self.db.table("links").select(
                "*, pages!inner(url)"
            ).eq("crawl_id", str(self.crawl_id)).execute()

            # Flatten the data structure
            if response.data:
                flattened = []
                for item in response.data:
                    page_data = item.pop("pages", {})
                    item["source_url"] = page_data.get("url", "Unknown")
                    flattened.append(item)
                return flattened
            return []
        except Exception as e:
            logger.error(f"Error fetching links: {e}")
            return []

    async def _fetch_images(self) -> List[Dict[str, Any]]:
        """Fetch all images for the crawl with page URLs."""
        try:
            # Join with pages table to get page URLs
            response = self.db.table("images").select(
                "*, pages!inner(url)"
            ).eq("crawl_id", str(self.crawl_id)).execute()

            # Flatten the data structure
            if response.data:
                flattened = []
                for item in response.data:
                    page_data = item.pop("pages", {})
                    item["page_url"] = page_data.get("url", "Unknown")
                    flattened.append(item)
                return flattened
            return []
        except Exception as e:
            logger.error(f"Error fetching images: {e}")
            return []

    async def _fetch_seo_metadata(self) -> List[Dict[str, Any]]:
        """Fetch all SEO metadata for the crawl with page URLs and content type."""
        try:
            # Join with pages table to get page URLs and content_type
            response = self.db.table("seo_metadata").select(
                "*, pages!inner(id, url, crawl_id, content_type, title)"
            ).eq("pages.crawl_id", str(self.crawl_id)).execute()

            # Flatten the data structure
            if response.data:
                flattened = []
                for item in response.data:
                    page_data = item.pop("pages", {})
                    item["page_id"] = page_data.get("id")
                    item["page_url"] = page_data.get("url", "Unknown")
                    item["content_type"] = page_data.get("content_type", "")
                    item["page_title"] = page_data.get("title", "")
                    flattened.append(item)
                return flattened
            return []
        except Exception as e:
            logger.error(f"Error fetching SEO metadata: {e}")
            return []

    def _add_issue(
        self,
        issue_type: str,
        severity: str,
        message: str,
        context: str,
        page_id: Optional[str] = None,
        pointer: Optional[str] = None
    ):
        """Add an issue to the issues list."""
        self.issues.append({
            "crawl_id": str(self.crawl_id),
            "page_id": page_id,
            "type": issue_type,
            "severity": severity,
            "message": message,
            "context": context,
            "pointer": pointer
        })

    # ==================== DETECTION METHODS ====================

    async def _detect_broken_links(self, links: List[Dict[str, Any]]):
        """Detect broken internal links (404 errors)."""
        broken_internal_links = [
            link for link in links
            if link.get("is_internal") and link.get("status_code") and link.get("status_code") >= 400
        ]

        for link in broken_internal_links:
            self._add_issue(
                issue_type="Links - Broken Internal Link",
                severity="critical",
                message=f"Internal link returns {link.get('status_code')} error. Update or remove this broken link.",
                context=link.get("source_url", "Unknown source"),
                pointer=link.get("target_url")
            )

    async def _detect_broken_images(self, images: List[Dict[str, Any]]):
        """Detect broken images (404 errors)."""
        broken_images = [
            img for img in images
            if img.get("is_broken") or (img.get("status_code") and img.get("status_code") >= 400)
        ]

        # Group by page to avoid spam
        pages_with_broken_images = {}
        for img in broken_images:
            page_url = img.get("page_url", "Unknown")
            if page_url not in pages_with_broken_images:
                pages_with_broken_images[page_url] = []
            pages_with_broken_images[page_url].append(img.get("src"))

        for page_url, image_srcs in pages_with_broken_images.items():
            count = len(image_srcs)
            self._add_issue(
                issue_type="Images - Broken Image",
                severity="high",
                message=f"{count} broken image{'s' if count > 1 else ''} on this page. Replace or remove broken images.",
                context=page_url,
                pointer=", ".join(image_srcs[:3]) + ("..." if count > 3 else "")
            )

    async def _detect_large_pages(self, pages: List[Dict[str, Any]]):
        """Detect pages larger than 3MB."""
        large_pages = [
            page for page in pages
            if page.get("page_size_bytes") and page.get("page_size_bytes") > 3 * 1024 * 1024
        ]

        for page in large_pages:
            size_mb = page.get("page_size_bytes", 0) / (1024 * 1024)
            self._add_issue(
                issue_type="Performance - Large Page Size",
                severity="high",
                message=f"Page size is {size_mb:.2f}MB (recommended: < 3MB). Optimize images, minify CSS/JS, and enable compression.",
                context=page.get("url", "Unknown URL"),
                page_id=page.get("id")
            )

    async def _detect_large_images(self, images: List[Dict[str, Any]]):
        """Detect images larger than 500KB."""
        # Note: size_bytes is not yet implemented in the images table
        # This check will be implemented in Phase 2 when we add size tracking
        # For now, we'll skip this check
        pass

    async def _detect_missing_alt_text(self, images: List[Dict[str, Any]]):
        """Detect images without alt text."""
        missing_alt_images = [
            img for img in images
            if not img.get("has_alt") or not img.get("alt") or img.get("alt", "").strip() == ""
        ]

        # Group by page to avoid spam
        pages_with_missing_alt = {}
        for img in missing_alt_images:
            page_url = img.get("page_url", "Unknown")
            if page_url not in pages_with_missing_alt:
                pages_with_missing_alt[page_url] = []
            pages_with_missing_alt[page_url].append(img.get("src"))

        for page_url, image_srcs in pages_with_missing_alt.items():
            count = len(image_srcs)
            self._add_issue(
                issue_type="Accessibility - Missing Alt Text",
                severity="high",
                message=f"{count} image{'s' if count > 1 else ''} missing alt text. Add descriptive alt text for screen readers and accessibility compliance.",
                context=page_url,
                pointer=", ".join(image_srcs[:3]) + ("..." if count > 3 else "")
            )

    async def _detect_thin_content(self, pages: List[Dict[str, Any]]):
        """Detect pages with less than 300 words. Skips non-HTML resources like PDFs."""
        thin_pages = [
            page for page in pages
            if page.get("word_count") is not None
            and page.get("word_count") < 300
            and self._is_html_page(page)  # Skip PDFs, images, etc.
        ]

        for page in thin_pages:
            word_count = page.get("word_count", 0)
            self._add_issue(
                issue_type="Content - Thin Content",
                severity="medium",
                message=f"Page has only {word_count} words (recommended: 300+ words). Expand content with valuable information to improve SEO and user engagement.",
                context=page.get("url", "Unknown URL"),
                page_id=page.get("id")
            )

    async def _detect_orphan_pages(self, pages: List[Dict[str, Any]], links: List[Dict[str, Any]]):
        """Detect pages with no internal links pointing to them. Skips non-HTML resources."""
        # Create a set of all target URLs from internal links
        linked_urls = {
            link.get("target_url")
            for link in links
            if link.get("is_internal") and link.get("target_url")
        }

        # Find pages not in the linked URLs set (only HTML pages)
        homepage_url = pages[0].get("url") if pages else None
        orphan_pages = [
            page for page in pages
            if page.get("url") not in linked_urls
            and page.get("url") != homepage_url  # Exclude homepage
            and self._is_html_page(page)  # Skip PDFs, images, etc.
        ]

        for page in orphan_pages:
            self._add_issue(
                issue_type="Content - Orphan Page",
                severity="medium",
                message="Page has no internal links pointing to it. Add internal links from related pages to improve discoverability and SEO.",
                context=page.get("url", "Unknown URL"),
                page_id=page.get("id")
            )

    async def _detect_duplicate_titles(self, seo_metadata: List[Dict[str, Any]]):
        """Detect pages with duplicate title tags.

        Uses URL normalization to avoid false positives from www vs non-www variants.
        """
        # Group pages by title, using normalized URLs to dedupe www vs non-www
        title_to_pages: Dict[str, Dict[str, str]] = {}  # title -> {normalized_url: original_url}

        for meta in seo_metadata:
            title = meta.get("title")
            page_url = meta.get("page_url", "Unknown")

            if not title or not title.strip():
                continue

            if title not in title_to_pages:
                title_to_pages[title] = {}

            # Use normalized URL as key to dedupe www vs non-www
            normalized = normalize_url_for_comparison(page_url)
            # Keep the first (original) URL we see for this normalized path
            if normalized not in title_to_pages[title]:
                title_to_pages[title][normalized] = page_url

        # Find titles used on multiple UNIQUE pages
        for title, pages_dict in title_to_pages.items():
            unique_page_count = len(pages_dict)
            if unique_page_count <= 1:
                continue  # Not a duplicate

            # Get the original URLs for display
            page_urls = list(pages_dict.values())

            self._add_issue(
                issue_type="SEO - Duplicate Title Tag",
                severity="high",
                message=f"Title '{title}' is used on {unique_page_count} pages. Create unique, descriptive titles for each page to improve search rankings.",
                context=", ".join(page_urls[:3]) + ("..." if unique_page_count > 3 else ""),
                pointer=title
            )

    async def _detect_duplicate_descriptions(self, seo_metadata: List[Dict[str, Any]]):
        """Detect pages with duplicate meta descriptions.

        Uses URL normalization to avoid false positives from www vs non-www variants.
        """
        # Group pages by description, using normalized URLs to dedupe
        desc_to_pages: Dict[str, Dict[str, str]] = {}  # desc -> {normalized_url: original_url}

        for meta in seo_metadata:
            desc = meta.get("meta_description")
            page_url = meta.get("page_url", "Unknown")

            if not desc or not desc.strip():
                continue

            if desc not in desc_to_pages:
                desc_to_pages[desc] = {}

            # Use normalized URL as key to dedupe www vs non-www
            normalized = normalize_url_for_comparison(page_url)
            if normalized not in desc_to_pages[desc]:
                desc_to_pages[desc][normalized] = page_url

        # Find descriptions used on multiple UNIQUE pages
        for desc, pages_dict in desc_to_pages.items():
            unique_page_count = len(pages_dict)
            if unique_page_count <= 1:
                continue  # Not a duplicate

            page_urls = list(pages_dict.values())

            # Truncate long descriptions for display
            display_desc = (desc[:50] + "...") if len(desc) > 50 else desc

            self._add_issue(
                issue_type="SEO - Duplicate Meta Description",
                severity="medium",
                message=f"Meta description '{display_desc}' is used on {unique_page_count} pages. Write unique, compelling descriptions to improve click-through rates.",
                context=", ".join(page_urls[:3]) + ("..." if unique_page_count > 3 else ""),
                pointer=desc
            )

    async def _detect_missing_h1(self, seo_metadata: List[Dict[str, Any]]):
        """Detect pages without H1 tags. Skips non-HTML resources like PDFs."""
        missing_h1_pages = [
            meta for meta in seo_metadata
            if (not meta.get("h1") or (isinstance(meta.get("h1"), str) and not meta.get("h1").strip()))
            and self._is_html_page({
                "content_type": meta.get("content_type"),
                "title": meta.get("page_title"),
                "url": meta.get("page_url")  # Include URL for .pdf extension check
            })
        ]

        for meta in missing_h1_pages:
            self._add_issue(
                issue_type="SEO - Missing H1 Heading",
                severity="medium",
                message="Page is missing an H1 heading. Add a descriptive H1 that clearly describes the page content for better SEO and accessibility.",
                context=meta.get("page_url", "Unknown URL"),
                page_id=meta.get("page_id")
            )

    async def _detect_multiple_h1s(self, seo_metadata: List[Dict[str, Any]]):
        """Detect pages with multiple H1 tags."""
        # Note: h1_count is not yet tracked in seo_metadata
        # This check will be implemented in Phase 2 when we enhance the crawler
        # For now, we'll skip this check
        pass


async def detect_and_store_issues(crawl_id: UUID, db_client=None) -> int:
    """
    Detect all issues for a crawl and store them in the database.
    Returns the number of issues detected.

    Args:
        crawl_id: The UUID of the crawl to analyze
        db_client: Optional database client (use service role client for Celery tasks)
    """
    # Use provided client or fall back to default
    db = db_client if db_client is not None else supabase_client

    detector = IssueDetector(crawl_id, db_client=db)
    issues = await detector.detect_all_issues()

    if not issues:
        logger.info(f"No issues detected for crawl {crawl_id}")
        return 0

    # Store issues in database
    try:
        # Delete existing issues for this crawl (if re-running detection)
        db.table("issues").delete().eq("crawl_id", str(crawl_id)).execute()

        # Insert new issues
        if issues:
            response = db.table("issues").insert(issues).execute()

            if hasattr(response, "error") and response.error is not None:
                logger.error(f"Error storing issues: {response.error}")
                return 0

        logger.info(f"Stored {len(issues)} issues for crawl {crawl_id}")
        return len(issues)

    except Exception as e:
        logger.error(f"Error storing issues for crawl {crawl_id}: {e}", exc_info=True)
        return 0
