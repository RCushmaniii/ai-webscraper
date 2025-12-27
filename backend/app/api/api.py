from fastapi import APIRouter
 
from app.api.routes import crawls, batches, users, health
from app.core.config import settings
 
api_router = APIRouter()
 
# Include all route modules
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(crawls.router, prefix="/crawls", tags=["crawls"])
if settings.ENABLE_BATCH_CRAWLS:
    api_router.include_router(batches.router, prefix="/batches", tags=["batches"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
