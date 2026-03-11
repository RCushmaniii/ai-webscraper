"""
Tests for the IssueDetector service.

All database calls are bypassed — we call the detection methods directly
with in-memory data to verify the detection logic itself.
"""

import pytest
from uuid import uuid4

from app.services.issue_detector import IssueDetector


@pytest.fixture
def detector(mock_db):
    """Create an IssueDetector with a mock DB client."""
    return IssueDetector(crawl_id=uuid4(), db_client=mock_db)


# ---------------------------------------------------------------------------
# Broken links
# ---------------------------------------------------------------------------

class TestDetectBrokenLinks:

    @pytest.mark.asyncio
    async def test_detect_broken_internal_link(self, detector):
        links = [
            {
                "is_internal": True,
                "status_code": 404,
                "source_url": "https://example.com/",
                "target_url": "https://example.com/missing",
            }
        ]
        await detector._detect_broken_links(links)
        assert len(detector.issues) == 1
        assert detector.issues[0]["type"] == "Links - Broken Internal Link"
        assert detector.issues[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_ignores_working_internal_link(self, detector):
        links = [
            {
                "is_internal": True,
                "status_code": 200,
                "source_url": "https://example.com/",
                "target_url": "https://example.com/about",
            }
        ]
        await detector._detect_broken_links(links)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_ignores_broken_external_link(self, detector):
        """Broken external links are not flagged (only internal)."""
        links = [
            {
                "is_internal": False,
                "status_code": 500,
                "source_url": "https://example.com/",
                "target_url": "https://other.com/down",
            }
        ]
        await detector._detect_broken_links(links)
        assert len(detector.issues) == 0


# ---------------------------------------------------------------------------
# Missing H1 / non-HTML skip
# ---------------------------------------------------------------------------

class TestDetectMissingH1:

    @pytest.mark.asyncio
    async def test_detect_missing_h1_on_html_page(self, detector):
        seo_metadata = [
            {
                "h1": None,
                "content_type": "text/html",
                "page_title": "My Page",
                "page_url": "https://example.com/page",
                "page_id": str(uuid4()),
            }
        ]
        await detector._detect_missing_h1(seo_metadata)
        assert len(detector.issues) == 1
        assert detector.issues[0]["type"] == "SEO - Missing H1 Heading"

    @pytest.mark.asyncio
    async def test_detect_missing_h1_skips_pdf(self, detector):
        """PDFs should never be flagged for missing H1."""
        seo_metadata = [
            {
                "h1": None,
                "content_type": "application/pdf",
                "page_title": "report.pdf (application/pdf)",
                "page_url": "https://example.com/report.pdf",
                "page_id": str(uuid4()),
            }
        ]
        await detector._detect_missing_h1(seo_metadata)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_detect_missing_h1_skips_image(self, detector):
        seo_metadata = [
            {
                "h1": None,
                "content_type": "image/png",
                "page_title": "logo.png",
                "page_url": "https://example.com/logo.png",
                "page_id": str(uuid4()),
            }
        ]
        await detector._detect_missing_h1(seo_metadata)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_no_issue_when_h1_present(self, detector):
        seo_metadata = [
            {
                "h1": "Welcome to Example",
                "content_type": "text/html",
                "page_title": "Example",
                "page_url": "https://example.com/",
                "page_id": str(uuid4()),
            }
        ]
        await detector._detect_missing_h1(seo_metadata)
        assert len(detector.issues) == 0


# ---------------------------------------------------------------------------
# Thin content
# ---------------------------------------------------------------------------

class TestDetectThinContent:

    @pytest.mark.asyncio
    async def test_detect_thin_content(self, detector):
        pages = [
            {
                "id": str(uuid4()),
                "url": "https://example.com/thin",
                "word_count": 50,
                "content_type": "text/html",
                "title": "Thin Page",
            }
        ]
        await detector._detect_thin_content(pages)
        assert len(detector.issues) == 1
        assert detector.issues[0]["type"] == "Content - Thin Content"
        assert detector.issues[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_no_thin_content_above_threshold(self, detector):
        pages = [
            {
                "id": str(uuid4()),
                "url": "https://example.com/rich",
                "word_count": 500,
                "content_type": "text/html",
                "title": "Rich Page",
            }
        ]
        await detector._detect_thin_content(pages)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_thin_content_skips_pdf(self, detector):
        """PDFs with low word count shouldn't be flagged."""
        pages = [
            {
                "id": str(uuid4()),
                "url": "https://example.com/doc.pdf",
                "word_count": 10,
                "content_type": "application/pdf",
                "title": "doc.pdf (application/pdf)",
            }
        ]
        await detector._detect_thin_content(pages)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_thin_content_boundary_299_words(self, detector):
        """299 words should be flagged (threshold is 300)."""
        pages = [
            {
                "id": str(uuid4()),
                "url": "https://example.com/borderline",
                "word_count": 299,
                "content_type": "text/html",
                "title": "Borderline",
            }
        ]
        await detector._detect_thin_content(pages)
        assert len(detector.issues) == 1

    @pytest.mark.asyncio
    async def test_thin_content_boundary_300_words(self, detector):
        """Exactly 300 words should NOT be flagged."""
        pages = [
            {
                "id": str(uuid4()),
                "url": "https://example.com/ok",
                "word_count": 300,
                "content_type": "text/html",
                "title": "OK Page",
            }
        ]
        await detector._detect_thin_content(pages)
        assert len(detector.issues) == 0


# ---------------------------------------------------------------------------
# Duplicate titles
# ---------------------------------------------------------------------------

class TestDetectDuplicateTitles:

    @pytest.mark.asyncio
    async def test_detect_duplicate_titles(self, detector):
        seo_metadata = [
            {"title": "Same Title", "page_url": "https://example.com/page1"},
            {"title": "Same Title", "page_url": "https://example.com/page2"},
        ]
        await detector._detect_duplicate_titles(seo_metadata)
        assert len(detector.issues) == 1
        assert detector.issues[0]["type"] == "SEO - Duplicate Title Tag"

    @pytest.mark.asyncio
    async def test_no_duplicate_when_titles_differ(self, detector):
        seo_metadata = [
            {"title": "Page One", "page_url": "https://example.com/page1"},
            {"title": "Page Two", "page_url": "https://example.com/page2"},
        ]
        await detector._detect_duplicate_titles(seo_metadata)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_ignores_empty_titles(self, detector):
        seo_metadata = [
            {"title": "", "page_url": "https://example.com/page1"},
            {"title": "", "page_url": "https://example.com/page2"},
        ]
        await detector._detect_duplicate_titles(seo_metadata)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_www_vs_non_www_not_duplicate(self, detector):
        """Same title on www and non-www of the SAME path should be deduplicated."""
        seo_metadata = [
            {"title": "Home", "page_url": "https://www.example.com/"},
            {"title": "Home", "page_url": "https://example.com/"},
        ]
        await detector._detect_duplicate_titles(seo_metadata)
        # www vs non-www for same page is normalized, so no duplicate
        assert len(detector.issues) == 0


# ---------------------------------------------------------------------------
# Missing alt text
# ---------------------------------------------------------------------------

class TestDetectMissingAltText:

    @pytest.mark.asyncio
    async def test_detect_missing_alt_text(self, detector):
        images = [
            {
                "has_alt": False,
                "alt": "",
                "src": "https://example.com/img1.jpg",
                "page_url": "https://example.com/",
            }
        ]
        await detector._detect_missing_alt_text(images)
        assert len(detector.issues) == 1
        assert detector.issues[0]["type"] == "Accessibility - Missing Alt Text"

    @pytest.mark.asyncio
    async def test_no_issue_when_alt_present(self, detector):
        images = [
            {
                "has_alt": True,
                "alt": "A nice photo",
                "src": "https://example.com/img1.jpg",
                "page_url": "https://example.com/",
            }
        ]
        await detector._detect_missing_alt_text(images)
        assert len(detector.issues) == 0

    @pytest.mark.asyncio
    async def test_whitespace_only_alt_counts_as_missing(self, detector):
        images = [
            {
                "has_alt": True,
                "alt": "   ",
                "src": "https://example.com/img1.jpg",
                "page_url": "https://example.com/",
            }
        ]
        await detector._detect_missing_alt_text(images)
        assert len(detector.issues) == 1

    @pytest.mark.asyncio
    async def test_groups_missing_alt_by_page(self, detector):
        """Multiple missing-alt images on one page should produce one issue."""
        images = [
            {"has_alt": False, "alt": "", "src": "/img1.jpg", "page_url": "https://example.com/"},
            {"has_alt": False, "alt": "", "src": "/img2.jpg", "page_url": "https://example.com/"},
            {"has_alt": False, "alt": "", "src": "/img3.jpg", "page_url": "https://example.com/"},
        ]
        await detector._detect_missing_alt_text(images)
        assert len(detector.issues) == 1
        assert "3 images" in detector.issues[0]["message"]


# ---------------------------------------------------------------------------
# _is_html_page helper
# ---------------------------------------------------------------------------

class TestIsHtmlPage:

    def test_html_page_returns_true(self, detector):
        page = {"content_type": "text/html", "title": "Page", "url": "https://example.com/"}
        assert detector._is_html_page(page) is True

    def test_pdf_returns_false(self, detector):
        page = {"content_type": "application/pdf", "title": "doc.pdf", "url": "https://example.com/doc.pdf"}
        assert detector._is_html_page(page) is False

    def test_json_returns_false(self, detector):
        page = {"content_type": "application/json", "title": "data", "url": "https://example.com/api/data.json"}
        assert detector._is_html_page(page) is False

    def test_url_extension_pdf_returns_false(self, detector):
        """Even with text/html content type, a .pdf URL should be treated as non-HTML."""
        page = {"content_type": "", "title": "report", "url": "https://example.com/report.pdf"}
        assert detector._is_html_page(page) is False

    def test_none_values_treated_as_html(self, detector):
        """Missing content_type and title should default to treating as HTML."""
        page = {"content_type": None, "title": None, "url": "https://example.com/page"}
        assert detector._is_html_page(page) is True
