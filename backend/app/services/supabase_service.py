from supabase import create_client, Client
from app.core.config import settings
from fastapi import Depends

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Supabase URL and key must be provided in environment variables")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class SupabaseService:
    """
    Service for interacting with Supabase
    """
    
    def __init__(self, client: Client = Depends(get_supabase_client)):
        self.client = client
    
    async def store_scraping_results(self, task_id: str, results: list):
        """
        Store scraping results in Supabase
        """
        self.client.table("scraping_tasks").update({
            "results": results,
            "status": "completed"
        }).eq("id", task_id).execute()
    
    async def update_task_status(self, task_id: str, status: str):
        """
        Update the status of a scraping task
        """
        self.client.table("scraping_tasks").update({
            "status": status
        }).eq("id", task_id).execute()
    
    async def get_task(self, task_id: str):
        """
        Get a task by ID
        """
        response = self.client.table("scraping_tasks").select("*").eq("id", task_id).execute()
        if response.data:
            return response.data[0]
        return None
