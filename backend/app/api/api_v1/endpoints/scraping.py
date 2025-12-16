from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from app.scrapers.base_scraper import ScraperFactory
from app.core.config import settings
from app.services.supabase_service import get_supabase_client

router = APIRouter()

class ScrapingRequest(BaseModel):
    url: HttpUrl
    selectors: Dict[str, str]
    scraper_type: str = "basic"  # basic, selenium, etc.
    pagination: Optional[Dict[str, Any]] = None
    max_pages: Optional[int] = 1

class ScrapingResponse(BaseModel):
    task_id: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    message: str

@router.post("/", response_model=ScrapingResponse)
async def scrape_website(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    supabase = Depends(get_supabase_client)
):
    """
    Endpoint to scrape a website based on provided selectors
    """
    if not settings.ENABLE_SELECTOR_SCRAPING:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        # Create scraper instance based on type
        scraper = ScraperFactory.get_scraper(request.scraper_type)
        
        # For immediate response (small scraping tasks)
        if request.max_pages == 1 and not request.pagination:
            data = await scraper.scrape(
                url=str(request.url),
                selectors=request.selectors
            )
            return ScrapingResponse(data=data, message="Scraping completed successfully")
        
        # For background tasks (larger scraping jobs)
        else:
            task_id = await scraper.schedule_scraping(
                url=str(request.url),
                selectors=request.selectors,
                pagination=request.pagination,
                max_pages=request.max_pages,
                supabase=supabase
            )
            return ScrapingResponse(task_id=task_id, message="Scraping task scheduled")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.get("/tasks/{task_id}", response_model=ScrapingResponse)
async def get_scraping_task(task_id: str, supabase = Depends(get_supabase_client)):
    """
    Get the status and results of a scraping task
    """
    if not settings.ENABLE_SELECTOR_SCRAPING:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        # Fetch task status from Supabase
        task = supabase.table("scraping_tasks").select("*").eq("id", task_id).execute()
        
        if not task.data:
            raise HTTPException(status_code=404, detail="Task not found")
            
        task_data = task.data[0]
        
        return ScrapingResponse(
            task_id=task_id,
            data=task_data.get("results"),
            message=f"Task status: {task_data.get('status')}"
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")
