from fastapi import APIRouter
from app.api.api_v1.endpoints import scraping, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(scraping.router, prefix="/scraping", tags=["scraping"])
