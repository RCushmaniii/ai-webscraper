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
        """Extract clean main content using Trafilatura"""
        # Use Trafilatura for smart content extraction
        main_text = extract(self.html, include_comments=False, include_tables=True)
        
        # Extract headings structure
        headings = self.extract_heading_structure()
        
        # Calculate content metrics
        word_count = len(main_text.split()) if main_text else 0
        
        return {
            'text': main_text or '',
            'word_count': word_count,
            'headings': headings,
            'reading_time': max(1, word_count // 200)  # Avg 200 words per minute
        }
    
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