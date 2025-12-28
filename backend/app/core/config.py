import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Web Scraper API"

    ENABLE_BATCH_CRAWLS: bool = os.getenv("ENABLE_BATCH_CRAWLS", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }

    ENABLE_SEO_AUDIT: bool = os.getenv("ENABLE_SEO_AUDIT", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }

    ENABLE_LLM: bool = os.getenv("ENABLE_LLM", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }

    ENABLE_SELECTOR_SCRAPING: bool = os.getenv("ENABLE_SELECTOR_SCRAPING", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }
    
    # Supabase settings (supports both new and legacy keys)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    # Prefer new secret key format (sb_secret_*), fallback to legacy service_role JWT
    SUPABASE_KEY: str = (
        os.getenv("SUPABASE_SECRET_KEY", "") or 
        os.getenv("SUPABASE_API_KEY", "") or 
        os.getenv("SUPABASE_KEY", "")
    )
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # React frontend (default)
        "http://localhost:3001",  # React frontend (alternative port)
        "http://localhost:3002",  # React frontend (alternative port)
        "http://localhost:8000",  # Backend for development
        "https://yourdomain.com",  # Production domain
    ]
    
    # Scraping settings
    DEFAULT_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    REQUEST_TIMEOUT: int = 30  # seconds
    
    # Celery settings for async tasks
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Storage settings
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage"))
    HTML_SNAPSHOTS_DIR: str = os.path.join(STORAGE_DIR, "html_snapshots")
    SCREENSHOTS_DIR: str = os.path.join(STORAGE_DIR, "screenshots")
    EXPORTS_DIR: str = os.path.join(STORAGE_DIR, "exports")
    
    # LLM settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

settings = Settings()
