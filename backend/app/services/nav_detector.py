"""
Navigation Detection Service

Analyzes HTML to identify "Main Navigation" links vs regular content links.
Uses scoring heuristics based on semantic HTML tags and common class names.

Usage:
    from app.services.nav_detector import NavDetector

    detector = NavDetector(html_content, base_url)
    nav_data = detector.extract_nav_links()

    # nav_data['primary_nav'] - High confidence navigation links (score >= 8)
    # nav_data['secondary_nav'] - Medium confidence (score 5-7)
    # nav_data['all_detected'] - All scored links
"""

from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


class NavDetector:
    """
    Detects and scores navigation links in HTML content.

    Scoring is based on:
    - Semantic HTML tags (<nav>, <header>, <footer>)
    - ARIA roles (role="navigation")
    - Common CSS class names (.navbar, .menu, .nav, etc.)
    - Link position and context
    """

    # Scoring configuration - higher scores = more likely to be navigation
    SELECTORS = [
        # Gold standard - explicit navigation
        {'css': 'nav a', 'score': 10},
        {'css': '[role="navigation"] a', 'score': 10},

        # Header region - usually main nav
        {'css': 'header a', 'score': 8},
        {'css': '.header a', 'score': 8},

        # Common navigation class patterns
        {'css': '.navbar a', 'score': 9},
        {'css': '.nav a', 'score': 9},
        {'css': '.menu a', 'score': 8},
        {'css': '.main-menu a', 'score': 9},
        {'css': '.main-nav a', 'score': 9},
        {'css': '.primary-nav a', 'score': 9},
        {'css': '.site-nav a', 'score': 9},
        {'css': '.top-nav a', 'score': 8},
        {'css': '.navigation a', 'score': 8},

        # Secondary navigation patterns
        {'css': '.sidebar a', 'score': 6},
        {'css': '.side-nav a', 'score': 6},
        {'css': 'aside nav a', 'score': 6},

        # Footer - often important links but sometimes legalese
        {'css': 'footer a', 'score': 5},
        {'css': '.footer a', 'score': 5},

        # Breadcrumbs - indicate page hierarchy
        {'css': '.breadcrumb a', 'score': 7},
        {'css': '.breadcrumbs a', 'score': 7},
        {'css': '[aria-label="breadcrumb"] a', 'score': 7},
    ]

    # URL patterns to exclude (usually not main pages)
    EXCLUDE_PATTERNS = [
        r'/tag/',
        r'/tags/',
        r'/category/',
        r'/author/',
        r'/page/\d+',
        r'/\d{4}/\d{2}/',  # Date-based URLs (blog posts)
        r'\?',  # Query strings
        r'#',   # Anchors
        r'mailto:',
        r'tel:',
        r'javascript:',
    ]

    # URL patterns that indicate primary pages
    PRIMARY_PAGE_PATTERNS = [
        r'^/$',                    # Homepage
        r'^/about',
        r'^/contact',
        r'^/services',
        r'^/products',
        r'^/pricing',
        r'^/features',
        r'^/solutions',
        r'^/blog$',               # Blog index (not individual posts)
        r'^/news$',
        r'^/team',
        r'^/careers',
        r'^/faq',
        r'^/help',
        r'^/support',
        r'^/docs$',
        r'^/documentation$',
    ]

    def __init__(self, html_content: str, base_url: str):
        """
        Initialize the navigation detector.

        Args:
            html_content: Raw HTML string to analyze
            base_url: Base URL for resolving relative links
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self._nav_links: Dict[str, int] = {}
        self._link_contexts: Dict[str, List[str]] = {}  # Track where each link was found

    def _normalize_url(self, href: str) -> Optional[str]:
        """
        Normalize a URL, handling relative paths and removing fragments.

        Args:
            href: The href attribute value

        Returns:
            Normalized absolute URL or None if invalid
        """
        if not href:
            return None

        # Skip non-HTTP links
        if any(href.startswith(p) for p in ['mailto:', 'tel:', 'javascript:', '#']):
            return None

        try:
            # Resolve relative URLs
            full_url = urljoin(self.base_url, href)
            parsed = urlparse(full_url)

            # Remove fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            # Remove trailing slash for consistency (except for root)
            if normalized.endswith('/') and parsed.path != '/':
                normalized = normalized[:-1]

            return normalized
        except Exception:
            return None

    def _should_exclude(self, url: str) -> bool:
        """
        Check if URL should be excluded based on patterns.

        Args:
            url: The URL to check

        Returns:
            True if URL should be excluded
        """
        parsed = urlparse(url)
        path = parsed.path

        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _is_primary_page_pattern(self, url: str) -> bool:
        """
        Check if URL matches known primary page patterns.

        Args:
            url: The URL to check

        Returns:
            True if URL looks like a primary page
        """
        parsed = urlparse(url)
        path = parsed.path.lower()

        for pattern in self.PRIMARY_PAGE_PATTERNS:
            if re.match(pattern, path, re.IGNORECASE):
                return True
        return False

    def _is_internal_link(self, url: str) -> bool:
        """
        Check if URL is internal to the base domain.

        Args:
            url: The URL to check

        Returns:
            True if internal link
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.base_domain or parsed.netloc == ''
        except Exception:
            return False

    def extract_nav_links(self) -> Dict:
        """
        Extract and score navigation links from the HTML.

        Returns:
            Dictionary containing:
            - primary_nav: List of high-confidence nav URLs (score >= 8)
            - secondary_nav: List of medium-confidence nav URLs (score 5-7)
            - all_detected: List of all detected links with scores
            - nav_structure: Dict mapping URLs to their contexts
        """
        # Process each selector
        for selector_config in self.SELECTORS:
            css = selector_config['css']
            score = selector_config['score']

            try:
                elements = self.soup.select(css)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = self._normalize_url(href)
                        if full_url and self._is_internal_link(full_url):
                            # Skip excluded patterns
                            if self._should_exclude(full_url):
                                continue

                            # Accumulate score (link may appear in multiple nav areas)
                            current_score = self._nav_links.get(full_url, 0)
                            self._nav_links[full_url] = current_score + score

                            # Track context
                            if full_url not in self._link_contexts:
                                self._link_contexts[full_url] = []
                            self._link_contexts[full_url].append(css)
            except Exception as e:
                logger.warning(f"Error processing selector '{css}': {e}")

        # Bonus points for primary page patterns
        for url in list(self._nav_links.keys()):
            if self._is_primary_page_pattern(url):
                self._nav_links[url] += 3

        # Sort by score (highest first)
        sorted_links = sorted(
            self._nav_links.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Categorize results
        all_detected = [
            {'url': url, 'score': score, 'contexts': self._link_contexts.get(url, [])}
            for url, score in sorted_links
        ]

        primary_nav = [item['url'] for item in all_detected if item['score'] >= 8]
        secondary_nav = [item['url'] for item in all_detected if 5 <= item['score'] < 8]

        return {
            'primary_nav': primary_nav,
            'secondary_nav': secondary_nav,
            'all_detected': all_detected,
            'nav_structure': self._link_contexts,
            'total_nav_links': len(all_detected)
        }

    def get_link_score(self, url: str) -> int:
        """
        Get the navigation score for a specific URL.

        Args:
            url: The URL to check

        Returns:
            Navigation score (0 if not found)
        """
        normalized = self._normalize_url(url)
        if normalized:
            return self._nav_links.get(normalized, 0)
        return 0

    def is_navigation_link(self, url: str, threshold: int = 5) -> bool:
        """
        Check if a URL is likely a navigation link.

        Args:
            url: The URL to check
            threshold: Minimum score to be considered navigation

        Returns:
            True if URL is likely a navigation link
        """
        return self.get_link_score(url) >= threshold


def detect_navigation(html_content: str, base_url: str) -> Dict:
    """
    Convenience function to detect navigation links.

    Args:
        html_content: Raw HTML string
        base_url: Base URL for the page

    Returns:
        Navigation detection results
    """
    detector = NavDetector(html_content, base_url)
    return detector.extract_nav_links()


def score_link(html_content: str, base_url: str, link_url: str) -> int:
    """
    Get the navigation score for a specific link.

    Args:
        html_content: Raw HTML string
        base_url: Base URL for the page
        link_url: The link URL to score

    Returns:
        Navigation score
    """
    detector = NavDetector(html_content, base_url)
    detector.extract_nav_links()  # Must run extraction first
    return detector.get_link_score(link_url)
