from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import asyncio
from contextlib import asynccontextmanager

from app.api.api import api_router
from app.core.config import settings
from app.services.crawl_monitor import check_and_fix_stale_crawls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
    
    yield
    
    # Shutdown: Cancel background task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Background monitoring task cancelled")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
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
