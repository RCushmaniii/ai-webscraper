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
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    # JWT_SECRET not needed - using JWKS endpoint for ES256 validation

    # SSL Certificate (for direct PostgreSQL connections if needed)
    # Note: Supabase Python client handles SSL automatically
    # This is only needed for direct psycopg2/SQLAlchemy connections
    SUPABASE_SSL_CERT_PATH: str = os.getenv(
        "SUPABASE_SSL_CERT_PATH",
        str(Path(__file__).parent.parent.parent / "certs" / "prod-ca-2021.crt")
    )
    
    # ============================================================================
    # CORS Configuration - Production-Ready Security
    # ============================================================================

    # Environment (development, staging, production)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # CORS Origins - CRITICAL: Lock down for production!
    # In production, ONLY allow your actual frontend domain(s)
    # NEVER use "*" wildcard in production - it defeats CORS security

    # Development CORS origins (permissive for local development)
    _DEV_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",       # React frontend (default)
        "http://localhost:3001",       # React frontend (alternative port)
        "http://localhost:3002",       # React frontend (alternative port)
        "http://localhost:5173",       # Vite default port
        "http://127.0.0.1:3000",       # Alternative localhost
        "http://127.0.0.1:5173",       # Vite alternative
    ]

    # Production CORS origins (strict - only actual domains)
    # TODO: Replace with your actual production domains before deployment!
    _PROD_CORS_ORIGINS: list[str] = [
        "https://yourdomain.com",           # Primary production domain
        "https://www.yourdomain.com",       # www subdomain
        "https://app.yourdomain.com",       # App subdomain (if applicable)
        # Add more production domains as needed
    ]

    # Staging CORS origins
    _STAGING_CORS_ORIGINS: list[str] = [
        "https://staging.yourdomain.com",
        "https://dev.yourdomain.com",
    ]

    # Get CORS origins from environment variable OR use defaults based on environment
    # Format: comma-separated list, e.g., "https://example.com,https://www.example.com"
    @property
    def BACKEND_CORS_ORIGINS(self) -> list[str]:
        """
        Get CORS origins based on environment.

        Priority:
        1. CORS_ORIGINS environment variable (if set)
        2. Environment-specific defaults (production/staging/development)

        IMPORTANT: In production, this should ONLY contain your actual frontend domains!
        """
        # If CORS_ORIGINS env var is set, use it (comma-separated)
        env_origins = os.getenv("CORS_ORIGINS", "").strip()
        if env_origins:
            return [origin.strip() for origin in env_origins.split(",") if origin.strip()]

        # Otherwise, use environment-specific defaults
        if self.ENVIRONMENT == "production":
            return self._PROD_CORS_ORIGINS
        elif self.ENVIRONMENT == "staging":
            return self._STAGING_CORS_ORIGINS + self._DEV_CORS_ORIGINS  # Include dev for testing
        else:  # development
            return self._DEV_CORS_ORIGINS
    
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
