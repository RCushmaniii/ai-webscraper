from celery import Celery
from app.core.config import settings
import asyncio
from app.scrapers.base_scraper import ScraperFactory
from app.services.supabase_service import SupabaseService, get_supabase_client

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="app.worker.scrape_task")
def scrape_task(task_id: str, url: str, selectors: dict, pagination: dict = None, max_pages: int = 1):
    """
    Background task to handle scraping jobs
    """
    if not settings.ENABLE_SELECTOR_SCRAPING:
        return {
            "status": "disabled",
            "task_id": task_id,
            "error": "Selector-based scraping is disabled in v1 scope.",
        }

    # Create event loop for async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Get Supabase client
    supabase = get_supabase_client()
    supabase_service = SupabaseService(supabase)
    
    try:
        # Update task status to running
        loop.run_until_complete(supabase_service.update_task_status(task_id, "running"))
        
        # Get appropriate scraper
        scraper_type = "basic"
        if pagination and pagination.get("requires_javascript", False):
            scraper_type = "selenium"
        
        scraper = ScraperFactory.get_scraper(scraper_type)
        
        all_results = []
        current_url = url
        
        # Scrape multiple pages if pagination is configured
        for page in range(max_pages):
            # Scrape current page
            results = loop.run_until_complete(scraper.scrape(current_url, selectors))
            all_results.extend(results)
            
            # Break if no pagination or we've reached the last page
            if not pagination or page >= max_pages - 1:
                break
                
            # Get next page URL
            if pagination.get("type") == "next_button":
                # This would need to be implemented with Selenium
                # For now, we'll just break
                break
            elif pagination.get("type") == "url_pattern":
                # Replace page number in URL pattern
                current_url = pagination["pattern"].format(page=page+2)  # +2 because we start at page 1
            else:
                break
        
        # Store results in Supabase
        loop.run_until_complete(supabase_service.store_scraping_results(task_id, all_results))
        
        return {"status": "success", "task_id": task_id, "result_count": len(all_results)}
        
    except Exception as e:
        # Update task status to failed
        loop.run_until_complete(supabase_service.update_task_status(task_id, "failed"))
        return {"status": "error", "task_id": task_id, "error": str(e)}
    
    finally:
        loop.close()
