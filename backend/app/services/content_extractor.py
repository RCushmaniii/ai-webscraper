# backend/app/services/content_extractor.py
import re
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from trafilatura import extract, extract_metadata
from urllib.parse import urljoin, urlparse
import requests

class SmartContentExtractor:
    def __init__(self, html_content: str, url: str):
        self.html = html_content
        self.url = url
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
    def extract_all_data(self) -> Dict:
        """Extract all relevant data from the page"""
        return {
            'content': self.extract_main_content(),
            'seo': self.extract_seo_data(),
            'technical': self.extract_technical_data(),
            'links': self.extract_links(),
            'images': self.extract_images(),
            'metadata': self.extract_page_metadata()
        }
    
    def extract_main_content(self) -> Dict:
        """
        Extract ALL visible text content from the page body.

        This extracts the full page copy (hero to footer) for SEO auditing,
        not just article content. Marketing pages need all their copy captured.
        """
        # Get full page text (all visible content from body)
        full_text = self._extract_full_page_text()

        # Also get Trafilatura extraction for article-style content (backup)
        trafilatura_text = extract(self.html, include_comments=False, include_tables=True)

        # Use the longer of the two - full page text is usually what we want
        # but Trafilatura can sometimes be better for article pages
        if full_text and trafilatura_text:
            main_text = full_text if len(full_text) >= len(trafilatura_text) else trafilatura_text
        else:
            main_text = full_text or trafilatura_text or ''

        # Extract headings structure
        headings = self.extract_heading_structure()

        # Calculate content metrics
        word_count = len(main_text.split()) if main_text else 0

        return {
            'text': main_text,
            'full_page_text': full_text,  # Always include full page text
            'word_count': word_count,
            'headings': headings,
            'reading_time': max(1, word_count // 200)  # Avg 200 words per minute
        }

    def _extract_full_page_text(self) -> str:
        """
        Extract ALL visible text from the page body.

        This is designed for marketing pages where you need:
        - Hero section copy
        - Feature descriptions
        - Testimonials
        - CTAs
        - Footer content

        Excludes: scripts, styles, hidden elements, navigation (optionally)
        """
        # Create a copy of soup to avoid modifying original
        soup_copy = BeautifulSoup(str(self.soup), 'html.parser')

        # Remove elements that don't contain useful text content
        for element in soup_copy.find_all(['script', 'style', 'noscript', 'svg', 'iframe']):
            element.decompose()

        # Remove hidden elements
        for element in soup_copy.find_all(attrs={'style': re.compile(r'display\s*:\s*none', re.I)}):
            element.decompose()
        for element in soup_copy.find_all(attrs={'hidden': True}):
            element.decompose()
        for element in soup_copy.find_all(class_=re.compile(r'hidden|visually-hidden|sr-only', re.I)):
            element.decompose()

        # Get the body content (or whole document if no body)
        body = soup_copy.find('body') or soup_copy

        # Extract text with some structure preserved
        text_parts = []

        # Process block-level elements to maintain structure
        block_elements = ['p', 'div', 'section', 'article', 'main', 'header', 'footer',
                         'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th',
                         'blockquote', 'figcaption', 'address']

        for element in body.find_all(block_elements):
            # Get direct text content (not from nested block elements)
            text = element.get_text(separator=' ', strip=True)
            if text and len(text) > 2:  # Skip very short strings
                # Clean up excessive whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                if text not in text_parts:  # Avoid duplicates
                    text_parts.append(text)

        # Join with double newlines for paragraph separation
        full_text = '\n\n'.join(text_parts)

        # Final cleanup
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)  # Max 2 newlines
        full_text = re.sub(r' {2,}', ' ', full_text)  # Max 1 space

        return full_text.strip()
    
    def extract_seo_data(self) -> Dict:
        """Extract SEO elements"""
        return {
            'title': self.get_meta_content('title'),
            'meta_description': self.get_meta_content('description'),
            'meta_keywords': self.get_meta_content('keywords'),
            'canonical': self.get_canonical_url(),
            'og_title': self.get_meta_content('og:title'),
            'og_description': self.get_meta_content('og:description'),
            'og_image': self.get_meta_content('og:image'),
            'robots': self.get_meta_content('robots'),
            'schema_markup': self.extract_schema_markup(),
            'title_length': len(self.get_meta_content('title') or ''),
            'description_length': len(self.get_meta_content('description') or '')
        }
    
    def extract_technical_data(self) -> Dict:
        """Extract technical SEO elements"""
        return {
            'h1_count': len(self.soup.find_all('h1')),
            'h2_count': len(self.soup.find_all('h2')),
            'h3_count': len(self.soup.find_all('h3')),
            'image_count': len(self.soup.find_all('img')),
            'images_without_alt': len([img for img in self.soup.find_all('img') if not img.get('alt')]),
            'internal_links': self.count_internal_links(),
            'external_links': self.count_external_links(),
            'page_size_kb': len(self.html) / 1024,
            'has_viewport_meta': bool(self.soup.find('meta', attrs={'name': 'viewport'})),
            'has_lang_attribute': bool(self.soup.find('html', attrs={'lang': True}))
        }
    
    def extract_links(self) -> List[Dict]:
        """Extract and analyze all links"""
        links = []
        base_domain = urlparse(self.url).netloc
        
        for link in self.soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(self.url, href)
            parsed_url = urlparse(full_url)
            
            links.append({
                'url': full_url,
                'text': link.get_text(strip=True),
                'title': link.get('title', ''),
                'is_internal': parsed_url.netloc == base_domain or parsed_url.netloc == '',
                'is_external': parsed_url.netloc != base_domain and parsed_url.netloc != '',
                'status': None  # Will be checked later
            })
        
        return links
    
    def extract_images(self) -> List[Dict]:
        """Extract image data"""
        images = []
        for img in self.soup.find_all('img'):
            src = img.get('src', '')
            if src:
                full_url = urljoin(self.url, src)
                images.append({
                    'src': full_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width'),
                    'height': img.get('height'),
                    'has_alt': bool(img.get('alt')),
                    'loading': img.get('loading', '')
                })
        return images
    
    def get_meta_content(self, name: str) -> Optional[str]:
        """Get meta tag content by name"""
        # Try name attribute first
        meta = self.soup.find('meta', attrs={'name': name})
        if meta:
            return meta.get('content')
        
        # Try property attribute (for Open Graph)
        meta = self.soup.find('meta', attrs={'property': name})
        if meta:
            return meta.get('content')
        
        # Special case for title
        if name == 'title':
            title_tag = self.soup.find('title')
            return title_tag.get_text(strip=True) if title_tag else None
        
        return None
    
    def extract_heading_structure(self) -> List[Dict]:
        """Extract heading hierarchy"""
        headings = []
        for i in range(1, 7):  # h1 to h6
            for heading in self.soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text(strip=True),
                    'length': len(heading.get_text(strip=True))
                })
        return headings
    
    def get_canonical_url(self) -> Optional[str]:
        """Get canonical URL"""
        canonical = self.soup.find('link', attrs={'rel': 'canonical'})
        return canonical.get('href') if canonical else None
    
    def extract_schema_markup(self) -> List[Dict]:
        """Extract JSON-LD schema markup"""
        schemas = []
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                import json
                schema_data = json.loads(script.string)
                schemas.append(schema_data)
            except (json.JSONDecodeError, AttributeError):
                continue
        return schemas
    
    def count_internal_links(self) -> int:
        """Count internal links"""
        base_domain = urlparse(self.url).netloc
        count = 0
        for link in self.soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/') or base_domain in href:
                count += 1
        return count
    
    def count_external_links(self) -> int:
        """Count external links"""
        base_domain = urlparse(self.url).netloc
        count = 0
        for link in self.soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http') and base_domain not in href:
                count += 1
        return count
    
    def extract_page_metadata(self) -> Dict:
        """Extract general page metadata using Trafilatura"""
        try:
            metadata = extract_metadata(self.html)
            return {
                'author': metadata.author if metadata else None,
                'date': metadata.date if metadata else None,
                'description': metadata.description if metadata else None,
                'sitename': metadata.sitename if metadata else None,
                'tags': metadata.tags if metadata else [],
                'url': metadata.url if metadata else self.url
            }
        except Exception:
            return {}