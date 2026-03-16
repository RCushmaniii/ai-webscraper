"""
Semantic Skeleton Builder

Pure Python module — no LLM, no DB calls.
Extracts structural signals from HTML that the AI strategy evaluator needs:
H1, H2s, paragraph openers, CTA buttons, page purpose, language.
"""

import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# URL path → page purpose mapping
# Order matters: more specific patterns checked first
PAGE_PURPOSE_PATTERNS: List[tuple] = [
    # Lead generation / conversion
    (r"/(contact|consultation|book|booking|schedule|demo|get-started|signup|sign-up|pricing|quote|free-trial)", "lead_generation"),
    # E-commerce / product
    (r"/(shop|store|product|products|cart|checkout|buy)", "ecommerce"),
    # Educational / content
    (r"/(blog|articles?|resources?|faq|faqs|guides?|learn|how-to|tutorials?|knowledge)", "educational"),
    # Brand story
    (r"/(about|team|our-story|mission|values|who-we-are|careers?|jobs?)", "brand_story"),
    # Portfolio / case studies
    (r"/(portfolio|projects?|case-stud|work|our-work|results|clients?|testimonials?)", "portfolio"),
    # Legal / compliance
    (r"/(privacy|terms|legal|cookie|disclaimer|gdpr|accessibility)", "legal"),
    # Support / help
    (r"/(support|help|docs|documentation|status|troubleshoot)", "support"),
    # Services
    (r"/(services?|solutions?|offerings?|what-we-do|capabilities)", "services"),
    # News / events
    (r"/(news|press|media|events?|announcements?|updates?)", "news"),
    # Localized pages
    (r"^/(es|fr|de|pt|ja|zh|ko|it|nl|ru|ar|hi)(/|$)", "localized"),
]


def infer_page_purpose(url: str) -> str:
    """Infer the page's purpose from its URL path pattern.

    Returns a purpose string like 'homepage', 'lead_generation', 'educational', etc.
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/").lower()

    # Homepage
    if not path or path == "/":
        return "homepage"

    for pattern, purpose in PAGE_PURPOSE_PATTERNS:
        if re.search(pattern, path):
            return purpose

    return "general"


def extract_headings(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract H1 and H2 headings from parsed HTML."""
    h1_tags = soup.find_all("h1")
    h2_tags = soup.find_all("h2")

    h1_texts = [tag.get_text(strip=True) for tag in h1_tags if tag.get_text(strip=True)]
    h2_texts = [tag.get_text(strip=True) for tag in h2_tags if tag.get_text(strip=True)]

    return {
        "h1": h1_texts[:3],  # Cap at 3 (shouldn't be more than 1 ideally)
        "h2s": h2_texts[:10],
    }


def extract_first_sentences(soup: BeautifulSoup, max_paragraphs: int = 8) -> List[str]:
    """Extract the first sentence of each <p> block (up to max_paragraphs).

    Gives the AI a sense of the page's opening copy and messaging flow.
    """
    paragraphs = soup.find_all("p")
    sentences = []

    for p in paragraphs:
        text = p.get_text(strip=True)
        if not text or len(text) < 20:
            continue

        # Extract first sentence (split on period, exclamation, question mark)
        match = re.match(r"^(.+?[.!?])\s", text)
        if match:
            sentences.append(match.group(1))
        elif len(text) <= 200:
            sentences.append(text)
        else:
            sentences.append(text[:200] + "...")

        if len(sentences) >= max_paragraphs:
            break

    return sentences


def extract_cta_buttons(soup: BeautifulSoup) -> List[str]:
    """Extract CTA button text from the page.

    Looks for <button> elements and <a> tags with button-like classes.
    """
    cta_texts = []

    # <button> elements
    for btn in soup.find_all("button"):
        text = btn.get_text(strip=True)
        if text and len(text) < 100:
            cta_texts.append(text)

    # <a> tags with button/cta classes
    for a_tag in soup.find_all("a"):
        classes = " ".join(a_tag.get("class", []))
        if re.search(r"(btn|button|cta|action|primary)", classes, re.IGNORECASE):
            text = a_tag.get_text(strip=True)
            if text and len(text) < 100:
                cta_texts.append(text)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for t in cta_texts:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append(t)

    return unique[:8]


def detect_language(soup: BeautifulSoup) -> str:
    """Detect page language from <html lang="..."> attribute."""
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        lang = html_tag.get("lang", "").strip().lower()
        # Normalize to 2-letter code
        return lang[:2] if lang else "en"
    return "en"


def build_semantic_skeleton(
    page: Dict[str, Any],
    html_content: str,
) -> Optional[Dict[str, Any]]:
    """Build a compact semantic skeleton for AI strategy analysis.

    Args:
        page: Page data dict with url, title, meta_description, etc.
        html_content: Raw HTML content of the page.

    Returns:
        A compact JSON-serializable dict with structural signals,
        or None if the page can't be meaningfully analyzed.
    """
    if not html_content or len(html_content) < 100:
        return None

    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except Exception:
        return None

    url = page.get("url", "")
    purpose = infer_page_purpose(url)

    # Skip legal pages — no point critiquing a privacy policy's "conversion strategy"
    if purpose == "legal":
        return None

    headings = extract_headings(soup)
    first_sentences = extract_first_sentences(soup)
    cta_buttons = extract_cta_buttons(soup)
    language = detect_language(soup)

    # Only return if there's enough content to analyze
    if not headings["h1"] and not headings["h2s"] and not first_sentences:
        return None

    skeleton = {
        "url": url,
        "title": page.get("title", ""),
        "meta_description": page.get("meta_description", ""),
        "inferred_purpose": purpose,
        "language": language,
        "headings": headings,
        "paragraph_openers": first_sentences,
        "cta_buttons": cta_buttons,
    }

    return skeleton
