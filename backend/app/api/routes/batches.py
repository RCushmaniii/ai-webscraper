from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import logging
from datetime import datetime

from app.core.auth import get_current_user
from app.models.models import Batch, BatchCreate, BatchUpdate, BatchResponse, User
from app.services.worker import batch_crawl
from app.db.supabase import supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=BatchResponse)
async def create_batch(
    batch: BatchCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new batch crawl job.
    """
    # Generate a new UUID for this batch
    batch_id = uuid4()
    
    # Create batch record in database
    batch_data = {
        "id": str(batch_id),
        "user_id": str(current_user.id),
        "name": batch.name,
        "description": batch.description,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    try:
        # Insert batch into Supabase
        response = supabase_client.table("batches").insert(batch_data).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error creating batch: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to create batch")
        
        # Insert batch sites
        batch_sites = []
        for site in batch.sites:
            batch_sites.append({
                "id": str(uuid4()),
                "batch_id": str(batch_id),
                "url": site.url,
                "name": site.name,
                "status": "queued"
            })
        
        if batch_sites:
            sites_response = supabase_client.table("batch_sites").insert(batch_sites).execute()
            
            if hasattr(sites_response, "error") and sites_response.error is not None:
                logger.error(f"Error creating batch sites: {sites_response.error}")
                raise HTTPException(status_code=500, detail="Failed to create batch sites")
        
        # Start the batch crawl task in the background
        background_tasks.add_task(
            start_batch_task,
            batch_id=str(batch_id),
            user_id=str(current_user.id),
            site_urls=[site.url for site in batch.sites],
            config={
                "max_depth": batch.max_depth,
                "max_pages": batch.max_pages,
                "respect_robots_txt": batch.respect_robots_txt,
                "follow_external_links": batch.follow_external_links,
                "js_rendering": batch.js_rendering,
                "rate_limit": batch.rate_limit,
                "user_agent": batch.user_agent
            }
        )
        
        return {
            "id": batch_id,
            "user_id": current_user.id,
            "name": batch.name,
            "description": batch.description,
            "status": "queued",
            "created_at": datetime.now(),
            "site_count": len(batch.sites),
            "message": "Batch job queued successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")

@router.get("/", response_model=List[BatchResponse])
async def list_batches(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all batches for the current user.
    """
    try:
        query = supabase_client.table("batches").select("*").eq("user_id", str(current_user.id))
        
        if status:
            query = query.eq("status", status)
        
        response = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing batches: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list batches")
        
        # Enhance response with site counts
        result = []
        for batch in response.data:
            # Get site count for this batch
            sites_response = supabase_client.table("batch_sites").select("count").eq("batch_id", batch["id"]).execute()
            
            if hasattr(sites_response, "error") and sites_response.error is not None:
                logger.error(f"Error counting batch sites: {sites_response.error}")
                site_count = 0
            else:
                site_count = sites_response.count
            
            batch["site_count"] = site_count
            result.append(batch)
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing batches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list batches: {str(e)}")

@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific batch by ID.
    """
    try:
        response = supabase_client.table("batches").select("*").eq("id", str(batch_id)).eq("user_id", str(current_user.id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error getting batch: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to get batch")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        batch = response.data[0]
        
        # Get site count for this batch
        sites_response = supabase_client.table("batch_sites").select("count").eq("batch_id", str(batch_id)).execute()
        
        if hasattr(sites_response, "error") and sites_response.error is not None:
            logger.error(f"Error counting batch sites: {sites_response.error}")
            site_count = 0
        else:
            site_count = sites_response.count
        
        batch["site_count"] = site_count
        
        return batch
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch: {str(e)}")

@router.delete("/{batch_id}", response_model=Dict[str, Any])
async def delete_batch(
    batch_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a batch and all associated data.
    """
    try:
        # First check if the batch exists and belongs to the user
        response = supabase_client.table("batches").select("*").eq("id", str(batch_id)).eq("user_id", str(current_user.id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error checking batch: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to check batch")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Get all crawl IDs associated with this batch
        crawl_ids_response = supabase_client.table("crawls").select("id").eq("batch_id", str(batch_id)).execute()
        
        if hasattr(crawl_ids_response, "error") and crawl_ids_response.error is not None:
            logger.error(f"Error getting batch crawl IDs: {crawl_ids_response.error}")
        else:
            # Delete all associated crawls and their data
            for crawl in crawl_ids_response.data:
                crawl_id = crawl["id"]
                
                # Delete crawl data from various tables
                tables = ["pages", "links", "seo_metadata", "issues", "summaries"]
                
                for table in tables:
                    delete_response = supabase_client.table(table).delete().eq("crawl_id", crawl_id).execute()
                    if hasattr(delete_response, "error") and delete_response.error is not None:
                        logger.error(f"Error deleting from {table}: {delete_response.error}")
                
                # Delete the crawl itself
                delete_response = supabase_client.table("crawls").delete().eq("id", crawl_id).execute()
                
                if hasattr(delete_response, "error") and delete_response.error is not None:
                    logger.error(f"Error deleting crawl: {delete_response.error}")
                
                # Delete associated files
                from app.services.storage import delete_crawl_data
                await delete_crawl_data(UUID(crawl_id))
        
        # Delete batch sites
        delete_sites_response = supabase_client.table("batch_sites").delete().eq("batch_id", str(batch_id)).execute()
        
        if hasattr(delete_sites_response, "error") and delete_sites_response.error is not None:
            logger.error(f"Error deleting batch sites: {delete_sites_response.error}")
        
        # Finally delete the batch itself
        delete_response = supabase_client.table("batches").delete().eq("id", str(batch_id)).execute()
        
        if hasattr(delete_response, "error") and delete_response.error is not None:
            logger.error(f"Error deleting batch: {delete_response.error}")
            raise HTTPException(status_code=500, detail="Failed to delete batch")
        
        return {"message": "Batch deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete batch: {str(e)}")

@router.get("/{batch_id}/sites", response_model=List[Dict[str, Any]])
async def list_batch_sites(
    batch_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all sites in a batch.
    """
    try:
        # First check if the batch exists and belongs to the user
        batch_response = supabase_client.table("batches").select("*").eq("id", str(batch_id)).eq("user_id", str(current_user.id)).execute()
        
        if hasattr(batch_response, "error") and batch_response.error is not None:
            logger.error(f"Error checking batch: {batch_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check batch")
        
        if not batch_response.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Build query for batch sites
        query = supabase_client.table("batch_sites").select("*").eq("batch_id", str(batch_id))
        
        if status:
            query = query.eq("status", status)
        
        response = query.range(skip, skip + limit - 1).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing batch sites: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list batch sites")
        
        # Enhance with crawl information
        result = []
        for site in response.data:
            # Get associated crawl if it exists
            if site.get("crawl_id"):
                crawl_response = supabase_client.table("crawls").select("status,created_at,updated_at").eq("id", site["crawl_id"]).execute()
                
                if hasattr(crawl_response, "error") and crawl_response.error is not None:
                    logger.error(f"Error getting crawl info: {crawl_response.error}")
                elif crawl_response.data:
                    site["crawl_status"] = crawl_response.data[0]["status"]
                    site["crawl_created_at"] = crawl_response.data[0]["created_at"]
                    site["crawl_updated_at"] = crawl_response.data[0]["updated_at"]
            
            result.append(site)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing batch sites: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list batch sites: {str(e)}")

@router.get("/{batch_id}/summary", response_model=Dict[str, Any])
async def get_batch_summary(
    batch_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary of the batch results.
    """
    try:
        # First check if the batch exists and belongs to the user
        batch_response = supabase_client.table("batches").select("*").eq("id", str(batch_id)).eq("user_id", str(current_user.id)).execute()
        
        if hasattr(batch_response, "error") and batch_response.error is not None:
            logger.error(f"Error checking batch: {batch_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check batch")
        
        if not batch_response.data:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        batch = batch_response.data[0]
        
        # Get all sites in this batch
        sites_response = supabase_client.table("batch_sites").select("*").eq("batch_id", str(batch_id)).execute()
        
        if hasattr(sites_response, "error") and sites_response.error is not None:
            logger.error(f"Error getting batch sites: {sites_response.error}")
            raise HTTPException(status_code=500, detail="Failed to get batch sites")
        
        # Get all crawls associated with this batch
        crawl_ids = [site["crawl_id"] for site in sites_response.data if site.get("crawl_id")]
        
        # Prepare summary statistics
        summary = {
            "batch_id": str(batch_id),
            "name": batch["name"],
            "description": batch["description"],
            "status": batch["status"],
            "created_at": batch["created_at"],
            "updated_at": batch["updated_at"],
            "total_sites": len(sites_response.data),
            "completed_sites": sum(1 for site in sites_response.data if site.get("status") == "completed"),
            "failed_sites": sum(1 for site in sites_response.data if site.get("status") == "failed"),
            "in_progress_sites": sum(1 for site in sites_response.data if site.get("status") == "in_progress"),
            "queued_sites": sum(1 for site in sites_response.data if site.get("status") == "queued"),
            "total_pages": 0,
            "total_links": 0,
            "total_issues": 0,
            "broken_links": 0,
            "site_summaries": []
        }
        
        # Get statistics for each crawl
        for crawl_id in crawl_ids:
            # Get pages count
            pages_response = supabase_client.table("pages").select("count").eq("crawl_id", crawl_id).execute()
            if not hasattr(pages_response, "error") or pages_response.error is None:
                summary["total_pages"] += pages_response.count
            
            # Get links count
            links_response = supabase_client.table("links").select("count").eq("crawl_id", crawl_id).execute()
            if not hasattr(links_response, "error") or links_response.error is None:
                summary["total_links"] += links_response.count
            
            # Get broken links count
            broken_links_response = supabase_client.table("links").select("count").eq("crawl_id", crawl_id).eq("is_broken", True).execute()
            if not hasattr(broken_links_response, "error") or broken_links_response.error is None:
                summary["broken_links"] += broken_links_response.count
            
            # Get issues count
            issues_response = supabase_client.table("issues").select("count").eq("crawl_id", crawl_id).execute()
            if not hasattr(issues_response, "error") or issues_response.error is None:
                summary["total_issues"] += issues_response.count
            
            # Get crawl info
            crawl_response = supabase_client.table("crawls").select("*").eq("id", crawl_id).execute()
            if not hasattr(crawl_response, "error") or crawl_response.error is None and crawl_response.data:
                crawl = crawl_response.data[0]
                
                # Get site info
                site_info = next((site for site in sites_response.data if site.get("crawl_id") == crawl_id), None)
                
                if site_info:
                    summary["site_summaries"].append({
                        "site_id": site_info["id"],
                        "url": site_info["url"],
                        "name": site_info["name"],
                        "status": site_info["status"],
                        "crawl_id": crawl_id,
                        "pages_count": pages_response.count if not hasattr(pages_response, "error") or pages_response.error is None else 0,
                        "links_count": links_response.count if not hasattr(links_response, "error") or links_response.error is None else 0,
                        "issues_count": issues_response.count if not hasattr(issues_response, "error") or issues_response.error is None else 0,
                        "broken_links_count": broken_links_response.count if not hasattr(broken_links_response, "error") or broken_links_response.error is None else 0
                    })
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch summary: {str(e)}")

async def start_batch_task(batch_id: str, user_id: str, site_urls: List[str], config: Dict[str, Any]):
    """
    Start a batch crawl task and update the batch status.
    """
    try:
        # Update batch status to "in_progress"
        update_response = supabase_client.table("batches").update({
            "status": "in_progress",
            "updated_at": datetime.now().isoformat()
        }).eq("id", batch_id).execute()

        if hasattr(update_response, "error") and update_response.error is not None:
            logger.error(f"Error updating batch status: {update_response.error}")
            return

        # Start the Celery task
        task = batch_crawl.delay(batch_id, user_id, site_urls, config)
        
        # Update batch with task_id
        update_response = supabase_client.table("batches").update({"task_id": task.id}).eq("id", batch_id).execute()
        
        if hasattr(update_response, "error") and update_response.error is not None:
            logger.error(f"Error updating batch task_id: {update_response.error}")
        
    except Exception as e:
        logger.error(f"Error starting batch task: {e}")
        # Update batch status to "failed"
        supabase_client.table("batches").update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        }).eq("id", batch_id).execute()
