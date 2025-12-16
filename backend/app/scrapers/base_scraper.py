from abc import ABC, abstractmethod
import uuid
from typing import Dict, List, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
from app.core.config import settings

class BaseScraper(ABC):
    """Base abstract class for all scrapers"""
    
    @abstractmethod
    async def scrape(self, url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrape data from a URL using provided CSS selectors"""
        pass
    
    @abstractmethod
    async def schedule_scraping(self, url: str, selectors: Dict[str, str], 
                               pagination: Optional[Dict[str, Any]], 
                               max_pages: int, supabase: Any) -> str:
        """Schedule a scraping task for larger jobs"""
        pass

class BasicScraper(BaseScraper):
    """Basic scraper using BeautifulSoup and aiohttp"""
    
    async def scrape(self, url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrape data from a URL using provided CSS selectors"""
        headers = {"User-Agent": settings.DEFAULT_USER_AGENT}
        results = []
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch URL: {url}, status code: {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, "lxml")
                
                # Find all container elements if specified
                container_selector = selectors.get("container")
                containers = [soup] if not container_selector else soup.select(container_selector)
                
                for container in containers:
                    item_data = {}
                    
                    # Extract data using selectors
                    for field, selector in selectors.items():
                        if field == "container":
                            continue
                            
                        elements = container.select(selector)
                        if elements:
                            # Get text content from all matching elements
                            item_data[field] = [el.get_text(strip=True) for el in elements]
                            # If only one element, return as single value instead of list
                            if len(item_data[field]) == 1:
                                item_data[field] = item_data[field][0]
                        else:
                            item_data[field] = None
                    
                    if item_data:
                        results.append(item_data)
        
        return results
    
    async def schedule_scraping(self, url: str, selectors: Dict[str, str], 
                               pagination: Optional[Dict[str, Any]], 
                               max_pages: int, supabase: Any) -> str:
        """Schedule a scraping task for larger jobs"""
        task_id = str(uuid.uuid4())
        
        # Create a task record in Supabase
        supabase.table("scraping_tasks").insert({
            "id": task_id,
            "url": url,
            "selectors": selectors,
            "pagination": pagination,
            "max_pages": max_pages,
            "status": "pending",
            "results": []
        }).execute()
        
        # In a real implementation, you would queue this task with Celery
        # For now, we'll simulate by returning the task ID
        # from app.worker import scrape_task
        # scrape_task.delay(task_id, url, selectors, pagination, max_pages)
        
        return task_id

class SeleniumScraper(BaseScraper):
    """Advanced scraper using Selenium for JavaScript-heavy websites"""
    
    async def scrape(self, url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scrape data from a URL using Selenium and provided CSS selectors"""
        # This would be implemented with Selenium WebDriver
        # For now, we'll return a placeholder
        return [{"message": "Selenium scraper not fully implemented yet"}]
    
    async def schedule_scraping(self, url: str, selectors: Dict[str, str], 
                               pagination: Optional[Dict[str, Any]], 
                               max_pages: int, supabase: Any) -> str:
        """Schedule a selenium scraping task"""
        task_id = str(uuid.uuid4())
        
        # Create a task record in Supabase
        supabase.table("scraping_tasks").insert({
            "id": task_id,
            "url": url,
            "selectors": selectors,
            "pagination": pagination,
            "max_pages": max_pages,
            "status": "pending",
            "results": [],
            "scraper_type": "selenium"
        }).execute()
        
        # In a real implementation, you would queue this task with Celery
        
        return task_id

class ScraperFactory:
    """Factory class to create appropriate scraper instances"""
    
    @staticmethod
    def get_scraper(scraper_type: str) -> BaseScraper:
        """Get a scraper instance based on type"""
        if scraper_type == "selenium":
            return SeleniumScraper()
        else:
            return BasicScraper()  # Default
