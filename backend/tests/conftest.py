"""
Shared test fixtures for the ai-webscraper backend test suite.

All external dependencies (Supabase, httpx, Playwright, OpenAI) are mocked
so tests run fast and never hit real services.

IMPORTANT: We must mock app.db.supabase and app.core.config BEFORE any
app modules are imported, because they connect to real services at import time.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime


# ---------------------------------------------------------------------------
# Mock Supabase client
# ---------------------------------------------------------------------------

class MockSupabaseResponse:
    """Mimics the response object returned by supabase-py queries."""

    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class MockSupabaseTable:
    """Chainable mock that imitates supabase.table('x').select(...).eq(...).execute()."""

    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args, **kwargs):
        return self

    def insert(self, data, **kwargs):
        self._data = data if isinstance(data, list) else [data]
        return self

    def update(self, data, **kwargs):
        return self

    def delete(self):
        return self

    def eq(self, *args, **kwargs):
        return self

    def neq(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def execute(self):
        return MockSupabaseResponse(data=self._data)


class MockSupabaseClient:
    """Lightweight mock of the Supabase client."""

    def __init__(self):
        self._tables = {}

    def table(self, name: str):
        if name not in self._tables:
            self._tables[name] = MockSupabaseTable()
        return self._tables[name]

    def set_table_data(self, name: str, data: list):
        """Helper to pre-populate a table with test data."""
        self._tables[name] = MockSupabaseTable(data=data)


# ---------------------------------------------------------------------------
# Pre-import mocking: prevent real Supabase/config connections
# ---------------------------------------------------------------------------

# Create a mock settings object with all required attributes
_mock_settings = MagicMock()
_mock_settings.SUPABASE_URL = "https://fake.supabase.co"
_mock_settings.SUPABASE_KEY = "fake-key"
_mock_settings.SUPABASE_SERVICE_ROLE_KEY = "fake-service-key"
_mock_settings.STORAGE_DIR = "/tmp/test-storage"
_mock_settings.HTML_SNAPSHOTS_DIR = "/tmp/test-storage/html"
_mock_settings.DEFAULT_USER_AGENT = "TestBot/1.0"
_mock_settings.ENVIRONMENT = "development"
_mock_settings.BACKEND_CORS_ORIGINS = ["http://localhost:3000"]

# Mock the config module before anything imports it
_mock_config_module = MagicMock()
_mock_config_module.settings = _mock_settings
sys.modules.setdefault("app.core.config", _mock_config_module)

# Mock the supabase DB module so it doesn't try to connect
_shared_mock_db = MockSupabaseClient()
_mock_db_module = MagicMock()
_mock_db_module.supabase_client = _shared_mock_db
sys.modules.setdefault("app.db.supabase", _mock_db_module)

# Mock the storage module (it depends on config)
_mock_storage_module = MagicMock()
_mock_storage_module.store_html_snapshot = AsyncMock(return_value="fake/path.html")
sys.modules.setdefault("app.services.storage", _mock_storage_module)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Provide a fresh mock Supabase client for tests that need DB access."""
    return MockSupabaseClient()


@pytest.fixture
def make_crawl():
    """Factory fixture that creates a Crawl model instance with sensible defaults."""

    def _make(**overrides):
        from app.models.models import Crawl

        defaults = {
            "id": uuid4(),
            "user_id": uuid4(),
            "url": "https://example.com",
            "name": "Test Crawl",
            "max_depth": 2,
            "max_pages": 100,
            "respect_robots_txt": True,
            "follow_external_links": False,
            "max_external_links": 5,
            "js_rendering": False,
            "rate_limit": 2.0,
            "user_agent": None,
            "max_runtime_sec": 3600,
            "internal_depth": 2,
            "external_depth": 1,
            "status": "pending",
            "pages_crawled": 0,
            "total_links": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        defaults.update(overrides)
        return Crawl(**defaults)

    return _make


@pytest.fixture
def make_crawler(make_crawl, mock_db):
    """
    Factory fixture that returns a Crawler with external I/O mocked out.

    Usage:
        crawler = make_crawler()              # uses defaults
        crawler = make_crawler(url="https://other.com")  # override crawl fields
    """

    def _make(**crawl_overrides):
        crawl = make_crawl(**crawl_overrides)
        from app.services.crawler import Crawler
        crawler = Crawler(crawl, db_client=mock_db)
        return crawler

    return _make
