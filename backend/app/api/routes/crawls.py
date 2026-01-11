from fastapi import APIRouter, Depends, HTTPException, Query
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import logging
from datetime import datetime

from app.core.auth import get_current_user, get_auth_client
from app.core.config import settings
from app.models.models import Crawl, CrawlCreate, CrawlUpdate, CrawlResponse, User
from app.services.worker import crawl_site
from app.services.storage import get_file_content
from app.db.supabase import supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=CrawlResponse)
async def create_crawl(
    crawl: CrawlCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new crawl job.
    """
    # Generate a new UUID for this crawl
    logger.info(f"Received crawl request: {crawl}")
    crawl_id = uuid4()

    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # Create crawl record in database
        now = datetime.now()
        raw_data = crawl.model_dump()

        # Map model fields to ACTUAL database column names (based on existing schema)
        crawl_data = {
            "id": str(crawl_id),
            "user_id": str(current_user.id),
            "url": raw_data["url"],  # Direct mapping
            "max_depth": raw_data.get("max_depth", 2),
            "max_pages": raw_data.get("max_pages", 100),
            "respect_robots_txt": raw_data.get("respect_robots_txt", True),
            "follow_external_links": raw_data.get("follow_external_links", False),
            "js_rendering": raw_data.get("js_rendering", False),
            "rate_limit": raw_data.get("rate_limit", 2),
            "user_agent": raw_data.get("user_agent") or "AI WebScraper Bot",
            "concurrency": 5,
            "status": "queued",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        # If no name is provided, use the hostname from the URL
        if raw_data.get("name"):
            crawl_data["name"] = raw_data["name"]
        else:
            try:
                parsed_url = urlparse(raw_data["url"])
                crawl_data["name"] = parsed_url.hostname or "Untitled Crawl"
            except Exception:
                crawl_data["name"] = "Untitled Crawl"

        logger.debug(f"Inserting crawl data: {crawl_data}")

        # Insert into Supabase
        response = auth_client.table("crawls").insert(crawl_data).execute()

        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error creating crawl in DB: {response.error.message}")
            raise HTTPException(status_code=500, detail=f"Failed to create crawl: {response.error.message}")

        # Dispatch the crawl task to Celery
        crawl_site.delay(str(crawl_id))
        logger.info(f"Dispatched crawl task {crawl_id} to Celery.")

        # Fetch the newly created record to ensure a valid response
        fetch_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).single().execute()

        if hasattr(fetch_response, "error") and fetch_response.error is not None:
            logger.error(f"Failed to fetch created crawl: {fetch_response.error.message}")
            # The crawl was created, but we can't return it. This is a problem.
            raise HTTPException(status_code=500, detail="Crawl created but failed to retrieve.")

        return CrawlResponse(**fetch_response.data)
        
    except Exception as e:
        logger.exception(f"An unexpected error occurred in create_crawl for crawl_id {crawl_id}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/", response_model=List[CrawlResponse])
async def list_crawls(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all crawls for the current user.
    Auto-detects and marks stale crawls as failed.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()
        
        # STEP 1: Clean up stale crawls (running/queued/pending for > 30 minutes)
        from datetime import timedelta
        now = datetime.now()
        stale_threshold = now - timedelta(minutes=30)
        
        logger.info(f"Checking for stale crawls. Now: {now}, Threshold: {stale_threshold}")
        
        # Find stale crawls for this user
        stale_response = auth_client.table("crawls").select("id, name, status, updated_at").eq("user_id", str(current_user.id)).in_("status", ["running", "queued", "pending"]).execute()
        
        logger.info(f"Found {len(stale_response.data) if stale_response.data else 0} running/queued/pending crawls")
        
        if stale_response.data:
            stale_crawl_ids = []
            for crawl in stale_response.data:
                try:
                    updated_at = datetime.fromisoformat(crawl['updated_at'].replace('Z', '+00:00'))
                    updated_at_naive = updated_at.replace(tzinfo=None)
                    is_stale = updated_at_naive < stale_threshold
                    logger.info(f"Crawl '{crawl['name']}': updated_at={updated_at_naive}, is_stale={is_stale}")
                    
                    if is_stale:
                        stale_crawl_ids.append(crawl['id'])
                        logger.info(f"Marking stale crawl as failed: {crawl['name']} (id: {crawl['id']}, status: {crawl['status']})")
                except Exception as parse_error:
                    logger.warning(f"Error parsing updated_at for crawl {crawl['id']}: {parse_error}")
            
            # Bulk update stale crawls to failed status
            if stale_crawl_ids:
                for crawl_id in stale_crawl_ids:
                    auth_client.table("crawls").update({
                        "status": "failed",
                        "notes": "Crawl timed out (no activity for 30+ minutes)",
                        "completed_at": now.isoformat(),  # Fixed: Database uses completed_at (not finished_at)
                        "updated_at": now.isoformat()
                    }).eq("id", crawl_id).execute()
                logger.info(f"Marked {len(stale_crawl_ids)} stale crawls as failed")
        
        # STEP 2: Fetch crawls with optional status filter
        query = auth_client.table("crawls").select("*").eq("user_id", str(current_user.id))
        
        if status:
            query = query.eq("status", status)
        
        response = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing crawls: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list crawls")
        
        return response.data
        
    except Exception as e:
        logger.error(f"Error listing crawls: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list crawls: {str(e)}")

@router.get("/{crawl_id}", response_model=CrawlResponse)
async def get_crawl(
    crawl_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific crawl by ID.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()
        response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error getting crawl: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to get crawl")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting crawl: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get crawl: {str(e)}")

@router.post("/{crawl_id}/mark-failed", response_model=Dict[str, Any])
async def mark_crawl_failed(
    crawl_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Manually mark a stuck crawl as failed.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # Check if crawl exists and belongs to user
        response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        crawl = response.data[0]

        # Only allow marking non-terminal states as failed
        if crawl['status'] in ['completed', 'failed', 'cancelled']:
            raise HTTPException(status_code=400, detail=f"Cannot mark {crawl['status']} crawl as failed")

        # Update to failed status
        from datetime import datetime, timezone
        update_response = auth_client.table("crawls").update({
            'status': 'failed',
            'error': 'Manually marked as failed by user',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq("id", str(crawl_id)).execute()
        
        if hasattr(update_response, "error") and update_response.error is not None:
            raise HTTPException(status_code=500, detail="Failed to update crawl status")
        
        return {"message": "Crawl marked as failed", "crawl_id": str(crawl_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking crawl as failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark crawl as failed: {str(e)}")

@router.post("/{crawl_id}/stop", response_model=Dict[str, Any])
async def stop_crawl(
    crawl_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Stop a running or queued crawl.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()
        
        # Check if crawl exists and belongs to user
        response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")
        
        crawl = response.data[0]
        
        # Only allow stopping running or queued crawls
        if crawl['status'] not in ['running', 'queued', 'pending']:
            raise HTTPException(status_code=400, detail=f"Cannot stop crawl with status: {crawl['status']}")
        
        # Revoke the Celery task if it exists
        if crawl.get('task_id'):
            try:
                from app.services.worker import celery_app
                celery_app.control.revoke(crawl['task_id'], terminate=True, signal='SIGKILL')
                logger.info(f"Revoked Celery task {crawl['task_id']} for crawl {crawl_id}")
            except Exception as revoke_error:
                logger.warning(f"Error revoking Celery task: {revoke_error}")
        
        # Update crawl status to stopped
        from datetime import datetime
        update_response = auth_client.table("crawls").update({
            'status': 'stopped',
            'completed_at': datetime.now().isoformat(),  # Fixed: Database uses completed_at (not finished_at)
            'updated_at': datetime.now().isoformat()
        }).eq("id", str(crawl_id)).execute()
        
        if hasattr(update_response, "error") and update_response.error is not None:
            raise HTTPException(status_code=500, detail="Failed to update crawl status")
        
        logger.info(f"Stopped crawl {crawl_id}")
        return {"message": "Crawl stopped successfully", "crawl_id": str(crawl_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping crawl: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop crawl: {str(e)}")

@router.delete("/{crawl_id}", response_model=Dict[str, Any])
async def delete_crawl(
    crawl_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a crawl and all associated data.
    """
    try:
        logger.info(f"Attempting to delete crawl {crawl_id} for user {current_user.id}")

        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error checking crawl: {response.error}")
            raise HTTPException(status_code=500, detail=f"Failed to check crawl: {response.error}")
        
        if not response.data:
            logger.warning(f"Crawl {crawl_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Crawl not found")
        
        logger.info(f"Found crawl {crawl_id}, proceeding with deletion")
        
        # Delete the crawl and related data
        # Note: In a real implementation with proper foreign keys, this would cascade
        tables = ["pages", "links", "seo_metadata", "issues", "summaries"]
        
        for table in tables:
            try:
                logger.info(f"Deleting from table: {table}")
                delete_response = auth_client.table(table).delete().eq("crawl_id", str(crawl_id)).execute()
                if hasattr(delete_response, "error") and delete_response.error is not None:
                    logger.error(f"Error deleting from {table}: {delete_response.error}")
                    # Don't fail the entire operation for related table errors
                else:
                    logger.info(f"Successfully deleted from {table}")
            except Exception as table_error:
                logger.error(f"Exception deleting from {table}: {table_error}")
                # Continue with other tables

        # Finally delete the crawl itself
        logger.info("Deleting crawl record")
        delete_response = auth_client.table("crawls").delete().eq("id", str(crawl_id)).execute()
        
        if hasattr(delete_response, "error") and delete_response.error is not None:
            logger.error(f"Error deleting crawl: {delete_response.error}")
            raise HTTPException(status_code=500, detail=f"Failed to delete crawl: {delete_response.error}")
        
        logger.info("Successfully deleted crawl record")
        
        # Also delete associated files
        try:
            logger.info("Deleting associated files")
            from app.services.storage import delete_crawl_data
            await delete_crawl_data(crawl_id)
            logger.info("Successfully deleted associated files")
        except Exception as file_error:
            logger.warning(f"Error deleting files (non-fatal): {file_error}")
            # Don't fail the operation for file deletion errors
        
        logger.info(f"Successfully deleted crawl {crawl_id}")
        return {"message": "Crawl deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting crawl {crawl_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete crawl: {str(e)}")

@router.get("/{crawl_id}/pages", response_model=List[Dict[str, Any]])
async def list_crawl_pages(
    crawl_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    List all pages for a specific crawl.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Get pages for this crawl
        response = auth_client.table("pages").select("*").eq("crawl_id", str(crawl_id)).range(skip, skip + limit - 1).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing pages: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list pages")
        
        return response.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing pages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list pages: {str(e)}")

@router.get("/{crawl_id}/pages/{page_id}", response_model=Dict[str, Any])
async def get_page_detail(
    crawl_id: UUID,
    page_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information for a specific page including full content.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Get the specific page
        response = auth_client.table("pages").select("*").eq("id", str(page_id)).eq("crawl_id", str(crawl_id)).single().execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error getting page: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to get page")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Page not found")
        
        return response.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page detail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get page: {str(e)}")

@router.get("/{crawl_id}/links", response_model=List[Dict[str, Any]])
async def list_crawl_links(
    crawl_id: UUID,
    skip: int = 0,
    limit: int = 100,
    is_broken: Optional[bool] = None,
    is_internal: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all links for a specific crawl with optional filters.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Build query for links
        query = auth_client.table("links").select("*").eq("crawl_id", str(crawl_id))
        
        if is_broken is not None:
            query = query.eq("is_broken", is_broken)
        
        if is_internal is not None:
            query = query.eq("is_internal", is_internal)
        
        response = query.range(skip, skip + limit - 1).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing links: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list links")
        
        return response.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing links: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list links: {str(e)}")

@router.get("/{crawl_id}/images", response_model=List[Dict[str, Any]])
async def list_crawl_images(
    crawl_id: UUID,
    skip: int = 0,
    limit: int = 100,
    has_alt: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all images for a specific crawl with optional filters.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # Check crawl exists and belongs to user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Build query
        query = auth_client.table("images").select("*").eq("crawl_id", str(crawl_id))

        if has_alt is not None:
            query = query.eq("has_alt", has_alt)

        response = query.range(skip, skip + limit - 1).execute()

        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing images: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list images")

        return response.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")

@router.get("/{crawl_id}/issues", response_model=List[Dict[str, Any]])
async def list_crawl_issues(
    crawl_id: UUID,
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    issue_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all issues for a specific crawl with optional filters.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Build query for issues
        query = auth_client.table("issues").select("*").eq("crawl_id", str(crawl_id))
        
        if severity:
            query = query.eq("severity", severity)
        
        if issue_type:
            query = query.eq("issue_type", issue_type)
        
        response = query.range(skip, skip + limit - 1).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing issues: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list issues")
        
        return response.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing issues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list issues: {str(e)}")

@router.get("/{crawl_id}/summary", response_model=Dict[str, Any])
async def get_crawl_summary(
    crawl_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get the summary for a specific crawl.
    """
    if not settings.ENABLE_LLM:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Get summary for this crawl
        response = auth_client.table("summaries").select("*").eq("crawl_id", str(crawl_id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error getting summary: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to get summary")
        
        if not response.data:
            # If no summary exists, return empty summary data
            return {
                "crawl_id": str(crawl_id),
                "summary": "No summary available yet",
                "status": "pending",
                "total_pages": 0,
                "total_links": 0,
                "total_issues": 0
            }
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.get("/{crawl_id}/html/{page_id}", response_model=Dict[str, Any])
async def get_page_html(
    crawl_id: UUID,
    page_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get the HTML snapshot for a specific page.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Get page info
        page_response = auth_client.table("pages").select("*").eq("id", str(page_id)).eq("crawl_id", str(crawl_id)).execute()
        
        if hasattr(page_response, "error") and page_response.error is not None:
            logger.error(f"Error getting page: {page_response.error}")
            raise HTTPException(status_code=500, detail="Failed to get page")
        
        if not page_response.data:
            raise HTTPException(status_code=404, detail="Page not found")
        
        page = page_response.data[0]
        
        if not page.get("html_snapshot_path"):
            raise HTTPException(status_code=404, detail="HTML snapshot not found for this page")
        
        # Get the HTML content
        html_content = await get_file_content(page["html_snapshot_path"])
        
        if html_content is None:
            raise HTTPException(status_code=404, detail="HTML snapshot file not found")
        
        return {
            "page_id": page_id,
            "url": page["url"],
            "html_content": html_content.decode("utf-8")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting HTML snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get HTML snapshot: {str(e)}")

@router.get("/{crawl_id}/screenshot/{page_id}", response_model=Dict[str, str])
async def get_page_screenshot(
    crawl_id: UUID,
    page_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get the screenshot for a specific page.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Get page info
        page_response = auth_client.table("pages").select("*").eq("id", str(page_id)).eq("crawl_id", str(crawl_id)).execute()
        
        if hasattr(page_response, "error") and page_response.error is not None:
            logger.error(f"Error getting page: {page_response.error}")
            raise HTTPException(status_code=500, detail="Failed to get page")
        
        if not page_response.data:
            raise HTTPException(status_code=404, detail="Page not found")
        
        page = page_response.data[0]
        
        if not page.get("screenshot_path"):
            raise HTTPException(status_code=404, detail="Screenshot not found for this page")
        
        # Return the screenshot path - the frontend will use this to construct a URL
        return {
            "page_id": str(page_id),
            "url": page["url"],
            "screenshot_path": page["screenshot_path"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screenshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get screenshot: {str(e)}")

async def start_crawl_task(crawl_id: str, start_url: str, config: Dict[str, Any]):
    """
    Start a crawl task and update the crawl status.
    """
    try:
        # Update crawl status to "in_progress"
        update_response = supabase_client.table("crawls").update({"status": "in_progress", "updated_at": datetime.now().isoformat()}).eq("id", crawl_id).execute()
        
        if hasattr(update_response, "error") and update_response.error is not None:
            logger.error(f"Error updating crawl status: {update_response.error}")
            return
        
        # Start the Celery task
        task = crawl_site.delay(crawl_id)
        
        # Update crawl with task_id
        update_response = supabase_client.table("crawls").update({"task_id": task.id}).eq("id", crawl_id).execute()
        
        if hasattr(update_response, "error") and update_response.error is not None:
            logger.error(f"Error updating crawl task_id: {update_response.error}")
        
    except Exception as e:
        logger.error(f"Error starting crawl task: {e}")
        # Update crawl status to "failed"
        supabase_client.table("crawls").update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        }).eq("id", crawl_id).execute()

@router.get("/{crawl_id}/audit", response_model=Dict[str, Any])
async def get_comprehensive_audit(
    crawl_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get the comprehensive SEO audit results for a specific crawl.
    """
    if not settings.ENABLE_SEO_AUDIT:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # First check if the crawl exists and belongs to the user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Try to get comprehensive audit results
        try:
            response = auth_client.table("comprehensive_audits").select("*").eq("crawl_id", str(crawl_id)).order("created_at", desc=True).limit(1).execute()

            if hasattr(response, "error") and response.error is not None:
                logger.warning(f"Comprehensive audits table may not exist: {response.error}")
                # Fall back to basic audit data
                return await _get_basic_audit_data(crawl_id, auth_client)
            
            if response.data:
                audit_data = response.data[0]
                return {
                    "crawl_id": str(crawl_id),
                    "audit_date": audit_data.get("created_at"),
                    "overall_score": audit_data.get("overall_score", 0),
                    "priority_issues_count": audit_data.get("priority_issues_count", 0),
                    "priority_issues": audit_data.get("audit_data", {}).get("priority_issues", []),
                    "broken_links": audit_data.get("audit_data", {}).get("broken_links", {"count": 0}),
                    "content_freshness": audit_data.get("audit_data", {}).get("content_freshness", {"outdated_count": 0, "average_age_days": 0}),
                    "duplicate_content": audit_data.get("audit_data", {}).get("duplicate_content", {"groups": 0, "affected_pages": 0}),
                    "schema_markup": audit_data.get("audit_data", {}).get("schema_markup", {"pages_with_schema": 0, "types": []}),
                    "recommendations": audit_data.get("audit_data", {}).get("recommendations", []),
                    "status": "completed"
                }
        except Exception as e:
            logger.warning(f"Error accessing comprehensive audits: {e}")
            # Fall back to basic audit data
            return await _get_basic_audit_data(crawl_id, auth_client)

        # If no comprehensive audit exists, return basic audit data
        return await _get_basic_audit_data(crawl_id, auth_client)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comprehensive audit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get comprehensive audit: {str(e)}")

async def _get_basic_audit_data(crawl_id: UUID, auth_client) -> Dict[str, Any]:
    """
    Get basic audit data from existing tables when comprehensive audit data is not available.
    """
    try:
        # Get basic crawl stats
        crawl_response = auth_client.table("crawls").select("pages_crawled, total_links, status").eq("id", str(crawl_id)).execute()
        crawl_data = crawl_response.data[0] if crawl_response.data else {}

        # Get pages count
        pages_response = auth_client.table("pages").select("id, status_code").eq("crawl_id", str(crawl_id)).execute()
        pages_data = pages_response.data if pages_response.data else []

        # Get links count and broken links
        links_response = auth_client.table("links").select("id, is_broken, status_code").eq("crawl_id", str(crawl_id)).execute()
        links_data = links_response.data if links_response.data else []

        # Get issues count
        try:
            issues_response = auth_client.table("issues").select("id, severity").eq("crawl_id", str(crawl_id)).execute()
            issues_data = issues_response.data if issues_response.data else []
        except:
            issues_data = []
        
        # Calculate basic metrics
        total_pages = len(pages_data)
        successful_pages = len([p for p in pages_data if p.get("status_code") == 200])
        total_links = len(links_data)
        broken_links = len([l for l in links_data if l.get("is_broken") or (l.get("status_code") and l.get("status_code") >= 400)])
        high_priority_issues = len([i for i in issues_data if i.get("severity") in ["high", "critical"]])
        
        # Calculate basic SEO score
        score = 50  # Base score
        if total_pages > 0:
            success_rate = successful_pages / total_pages
            score += int(success_rate * 30)  # Up to 30 points for successful crawling
        
        if total_links > 0:
            link_health = 1 - (broken_links / total_links)
            score += int(link_health * 20)  # Up to 20 points for link health
        
        # Deduct points for issues
        score -= min(high_priority_issues * 5, 30)  # Deduct up to 30 points for issues
        score = max(0, min(100, score))  # Ensure score is between 0-100
        
        return {
            "crawl_id": str(crawl_id),
            "audit_date": None,
            "overall_score": score,
            "priority_issues": [
                {
                    "type": "Broken Links",
                    "description": f"Found {broken_links} broken links that need attention",
                    "count": broken_links
                }
            ] if broken_links > 0 else [],
            "broken_links": {
                "count": broken_links,
                "examples": []
            },
            "content_freshness": {
                "outdated_count": 0,
                "average_age_days": 0
            },
            "duplicate_content": {
                "groups": 0,
                "affected_pages": 0
            },
            "schema_markup": {
                "pages_with_schema": 0,
                "types": []
            },
            "recommendations": [
                {
                    "title": "Set up comprehensive SEO auditing",
                    "description": "Run the database migration to enable detailed SEO audit features",
                    "priority": "medium"
                }
            ] if crawl_data.get("status") == "completed" else [
                {
                    "title": "Complete the crawl",
                    "description": "Wait for the crawl to complete before viewing audit results",
                    "priority": "high"
                }
            ],
            "status": "basic" if crawl_data.get("status") == "completed" else "pending"
        }
        
    except Exception as e:
        logger.error(f"Error getting basic audit data: {e}")
        return {
            "crawl_id": str(crawl_id),
            "audit_date": None,
            "overall_score": 0,
            "priority_issues": [],
            "broken_links": {"count": 0},
            "content_freshness": {"outdated_count": 0, "average_age_days": 0},
            "duplicate_content": {"groups": 0, "affected_pages": 0},
            "schema_markup": {"pages_with_schema": 0, "types": []},
            "recommendations": [
                {
                    "title": "Database setup required",
                    "description": "Run the SEO audit database migration to enable full audit features",
                    "priority": "high"
                }
            ],
            "status": "error"
        }

@router.get("/{crawl_id}/pages/{page_id}/links", response_model=List[Dict[str, Any]])
async def list_page_links(
    crawl_id: UUID,
    page_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    List all links from a specific page.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # Check crawl exists and belongs to user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Get links for this page
        response = auth_client.table("links").select("*").eq("source_page_id", str(page_id)).execute()

        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing page links: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list page links")

        return response.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing page links: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list page links: {str(e)}")

@router.get("/{crawl_id}/pages/{page_id}/images", response_model=List[Dict[str, Any]])
async def list_page_images(
    crawl_id: UUID,
    page_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    List all images from a specific page.
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # Check crawl exists and belongs to user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Get images for this page
        response = auth_client.table("images").select("*").eq("page_id", str(page_id)).execute()

        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing page images: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list page images")

        return response.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing page images: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list page images: {str(e)}")

@router.get("/{crawl_id}/search", response_model=Dict[str, Any])
async def search_crawl_data(
    crawl_id: UUID,
    query: str = Query(..., min_length=2, description="Search query"),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Full-text search across pages, links, and images for a specific crawl.
    Returns results grouped by type (pages, links, images).
    """
    try:
        # Use authenticated client for RLS
        auth_client = get_auth_client()

        # Check crawl exists and belongs to user
        crawl_response = auth_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if hasattr(crawl_response, "error") and crawl_response.error is not None:
            logger.error(f"Error checking crawl: {crawl_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check crawl")

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Search pages using full-text search
        # Note: PostgreSQL full-text search uses to_tsvector and to_tsquery
        pages_query = auth_client.table("pages").select("*").eq("crawl_id", str(crawl_id))

        # For now, use simple text search until we set up proper full-text search
        # This will search in title and content_summary
        pages_response = pages_query.or_(f"title.ilike.%{query}%,content_summary.ilike.%{query}%,url.ilike.%{query}%").range(skip, skip + limit - 1).execute()

        # Search links by anchor text or URL
        links_query = auth_client.table("links").select("*").eq("crawl_id", str(crawl_id))
        links_response = links_query.or_(f"anchor_text.ilike.%{query}%,target_url.ilike.%{query}%").range(skip, skip + limit - 1).execute()

        # Search images by alt text or src
        images_query = auth_client.table("images").select("*").eq("crawl_id", str(crawl_id))
        images_response = images_query.or_(f"alt.ilike.%{query}%,src.ilike.%{query}%").range(skip, skip + limit - 1).execute()

        return {
            "query": query,
            "results": {
                "pages": pages_response.data if pages_response.data else [],
                "links": links_response.data if links_response.data else [],
                "images": images_response.data if images_response.data else []
            },
            "counts": {
                "pages": len(pages_response.data) if pages_response.data else 0,
                "links": len(links_response.data) if links_response.data else 0,
                "images": len(images_response.data) if images_response.data else 0
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching crawl data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search crawl data: {str(e)}")
