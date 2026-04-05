from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
import time
import logging
import asyncio
import os
from contextlib import asynccontextmanager
import sentry_sdk

from app.api.api import api_router
from app.core.config import settings

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    send_default_pii=True,
    environment=os.environ.get("ENVIRONMENT", "development"),
    traces_sample_rate=0.2,
)
from app.services.crawl_monitor import check_and_fix_stale_crawls
from app.services.storage import cleanup_old_storage
from app.middleware.rate_limiter import rate_limit_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Reduce verbosity of noisy libraries (only show warnings/errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Background task for monitoring stale crawls
async def monitor_stale_crawls():
    """Background task that runs every 10 minutes to check for stale crawls"""
    while True:
        try:
            logger.info("Running stale crawl check...")
            check_and_fix_stale_crawls()
            logger.info("Stale crawl check completed")
        except Exception as e:
            logger.error(f"Error in stale crawl monitor: {e}")
        
        # Wait 10 minutes before next check
        await asyncio.sleep(600)


async def daily_storage_cleanup():
    """Background task that runs once daily to purge storage older than 90 days"""
    while True:
        try:
            result = cleanup_old_storage(max_age_days=90)
            if result["crawls_cleaned"] > 0:
                logger.info(f"Storage cleanup freed {result['bytes_freed'] / 1024:.1f} KB")
        except Exception as e:
            logger.error(f"Error in storage cleanup: {e}")

        # Run once every 24 hours
        await asyncio.sleep(86400)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Run initial check and start background task
    logger.info("Starting up... Running initial stale crawl check")
    try:
        check_and_fix_stale_crawls()
    except Exception as e:
        logger.error(f"Error in initial stale crawl check: {e}")
    
    # Start background monitoring task
    task = asyncio.create_task(monitor_stale_crawls())
    logger.info("Started background stale crawl monitoring (runs every 10 minutes)")

    # Start daily storage cleanup (runs once on startup, then every 24h)
    cleanup_task = asyncio.create_task(daily_storage_cleanup())
    logger.info("Started daily storage cleanup (90-day retention)")

    yield

    # Shutdown: Cancel background tasks
    task.cancel()
    cleanup_task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Background monitoring task cancelled")
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("Storage cleanup task cancelled")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# 0. GZip Compression - Compress responses larger than 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# 1. CORS Middleware - Must be first to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Security Headers Middleware - Add security headers to all responses
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    host = request.headers.get("host", "")
    if not host.startswith("localhost") and not host.startswith("127.0.0.1"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# 3. Request Body Size Limit Middleware - Reject requests larger than 10MB
MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB

@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body too large. Maximum size is 10MB."}
        )
    return await call_next(request)

# 4. Rate Limiting Middleware - Apply rate limits based on subscription tier
# NOTE: Currently using in-memory limiter for development
# TODO: Switch to Redis-based limiter for production (see rate_limiter.py)
app.middleware("http")(rate_limit_middleware)

# 5. Request Logging Middleware - Log all requests for monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log request details
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )
        
        # Add custom header with processing time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        return response
        
    except Exception as e:
        # Log the exception
        process_time = time.time() - start_time
        logger.error(
            f"Request: {request.method} {request.url.path} "
            f"Error: {str(e)} "
            f"Duration: {process_time:.3f}s"
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "monitoring": "stale_crawl_check_active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
