import logging
import asyncio
from celery import Celery
from typing import Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
import ssl
from supabase import create_client

from app.core.config import settings
from app.models.models import Crawl, CrawlCreate
from app.services.crawler import Crawler
from app.db.supabase import supabase_client

# Configure logging
logger = logging.getLogger(__name__)

# Reduce verbosity of noisy libraries (only show warnings/errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Create service role client for Celery (bypasses RLS)
service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

# Log service role key initialization (first 20 chars only for security)
logger.info(f"Service client initialized with key: {settings.SUPABASE_SERVICE_ROLE_KEY[:20]}...")

# Configure Celery with SSL support for Upstash Redis
broker_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
}

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure SSL and connection settings for broker and backend
celery_app.conf.update(
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=broker_use_ssl,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_pool_limit=1,
    broker_heartbeat=None,
    broker_connection_timeout=30,
    result_backend_transport_options={
        'master_name': 'mymaster',
        'socket_keepalive': True,
        'socket_keepalive_options': {
            1: 1,  # TCP_KEEPIDLE
            2: 1,  # TCP_KEEPINTVL
            3: 5,  # TCP_KEEPCNT
        },
        'health_check_interval': 30,
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)

@celery_app.task(name="crawl_site")
def crawl_site(crawl_id: str) -> Dict[str, Any]:
    """
    Celery task to crawl a site asynchronously.

    Args:
        crawl_id: UUID of the crawl

    Returns:
        Dict with crawl results summary
    """
    logger.info(f"Starting crawl task for crawl_id: {crawl_id}")

    try:
        # 1. Fetch crawl data from Supabase using service role (bypasses RLS)
        logger.info(f"Fetching crawl {crawl_id} using service role client...")
        
        try:
            response = service_client.table("crawls").select("*").eq("id", crawl_id).single().execute()
        except Exception as fetch_error:
            # Check if this is an RLS issue or a missing crawl
            error_msg = str(fetch_error)
            if "0 rows" in error_msg or "PGRST116" in error_msg:
                # Could be either RLS blocking or crawl doesn't exist
                # Try to fetch without .single() to see if it's an RLS issue
                logger.warning(f"Single fetch failed, checking if crawl exists at all...")
                check_response = service_client.table("crawls").select("id").eq("id", crawl_id).execute()
                
                if check_response.data and len(check_response.data) > 0:
                    logger.error(f"Crawl {crawl_id} exists but service role can't access it - RLS issue!")
                    raise ValueError(f"RLS blocking service role access to crawl {crawl_id}. Check RLS policies.")
                else:
                    logger.error(f"Crawl {crawl_id} does not exist in database (may have been deleted).")
                    raise ValueError(f"Crawl not found: {crawl_id}")
            else:
                # Some other error
                logger.error(f"Unexpected error fetching crawl: {error_msg}")
                raise

        if response.data is None:
            logger.error(f"Crawl with id {crawl_id} not found (response.data is None).")
            raise ValueError(f"Crawl not found: {crawl_id}")

        # 2. Instantiate Crawl model
        crawl_model = Crawl(**response.data)

        # 2.5. Mark crawl as running (removed started_at - column doesn't exist in DB)
        service_client.table("crawls").update({
            "status": "running",
            "updated_at": datetime.now().isoformat()
        }).eq("id", crawl_id).execute()

        logger.info(f"Starting crawler for {crawl_model.url}")

        # 3. Instantiate Crawler with the model and service client (bypasses RLS)
        crawler = Crawler(crawl=crawl_model, db_client=service_client)

        # 4. Run the crawl (asynchronously)
        asyncio.run(crawler.start())

        logger.info(f"Crawl finished for {crawl_id}. Pages crawled: {crawler.pages_crawled}")

        progress = crawler.get_progress()

        # 5. Update crawl status and final metrics in database
        # IMPORTANT: Mark as failed if 0 pages were crawled
        if progress.pages_crawled == 0:
            final_update = {
                "status": "failed",
                "pages_crawled": 0,
                "total_links": 0,
                "error": "Crawl completed but no pages were successfully crawled. This could be due to: robots.txt blocking, connection issues, or invalid URL.",
                "completed_at": datetime.now().isoformat(),  # Fixed: Use completed_at (database field name)
                "updated_at": datetime.now().isoformat()
            }
            logger.warning(f"Crawl {crawl_id} completed with 0 pages - marking as failed")
        else:
            final_update = {
                "status": "completed",
                "pages_crawled": progress.pages_crawled,
                "total_links": len(crawler.visited_urls) + len(crawler.url_queue),
                "completed_at": datetime.now().isoformat(),  # Fixed: Use completed_at (database field name)
                "updated_at": datetime.now().isoformat()
            }

        service_client.table("crawls").update(final_update).eq("id", crawl_id).execute()

        # 6. Run Phase 1 issue detection (only if crawl was successful)
        if progress.pages_crawled > 0:
            try:
                from app.services.issue_detector import detect_and_store_issues
                issues_count = asyncio.run(detect_and_store_issues(UUID(crawl_id)))
                logger.info(f"Detected and stored {issues_count} issues for crawl {crawl_id}")
            except Exception as issue_error:
                logger.error(f"Error detecting issues for {crawl_id}: {issue_error}")

        # 7. Run comprehensive SEO audit
        if settings.ENABLE_SEO_AUDIT:
            try:
                from app.services.seo_auditor import SEOAuditor
                auditor = SEOAuditor(crawl_id)
                audit_results = asyncio.run(auditor.run_comprehensive_audit())
                logger.info(
                    f"Completed SEO audit for crawl {crawl_id} with score: {audit_results.get('overall_score', 0)}"
                )
            except Exception as audit_error:
                logger.error(f"Error running SEO audit for {crawl_id}: {audit_error}")

        return {
            "crawl_id": crawl_id,
            "status": "completed",
            "pages_crawled": progress.pages_crawled,
        }

    except Exception as e:
        logger.error(f"Error during crawl for {crawl_id}: {e}", exc_info=True)

        # Provide helpful error message
        error_msg = str(e)
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            error_msg = f"Connection failed: {error_msg}. The site may be blocking crawlers or is unreachable."
        elif "SSL" in error_msg or "certificate" in error_msg.lower():
            error_msg = f"SSL/Certificate error: {error_msg}. The site's security certificate may be invalid."
        elif "robots" in error_msg.lower():
            error_msg = f"Robots.txt blocking: {error_msg}. The site disallows crawling."

        service_client.table("crawls").update({
            "status": "failed",
            "error": error_msg[:500],  # Limit error length
            "completed_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).eq("id", crawl_id).execute()

        return {
            "crawl_id": crawl_id,
            "status": "failed",
            "error": error_msg
        }

@celery_app.task(name="batch_crawl")
def batch_crawl(batch_id: str, user_id: str, site_urls: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to crawl multiple sites in a batch.
    """
    logger.info(f"Starting batch crawl for {len(site_urls)} sites with batch ID {batch_id}")
    
    results = {
        "batch_id": batch_id,
        "total_sites": len(site_urls),
        "crawl_ids": []
    }

    for url in site_urls:
        crawl_id = uuid4()

        crawl_config = CrawlCreate(url=url, **config)
        crawl_data = {
            "id": str(crawl_id),
            "user_id": user_id,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **crawl_config.model_dump(),
            "name": f"Batch crawl for {url}",
        }
        
        try:
            service_client.table("crawls").insert(crawl_data).execute()
            crawl_site.delay(str(crawl_id))
            results["crawl_ids"].append(str(crawl_id))
        except Exception as e:
            logger.error(f"Failed to create or dispatch crawl for {url}: {e}")

    return results

@celery_app.task(name="generate_summary")
def generate_summary(crawl_id: str) -> Dict[str, Any]:
    """
    Celery task to generate a summary for a completed crawl.
    """
    if not settings.ENABLE_LLM:
        return {
            "crawl_id": crawl_id,
            "summary_generated": False,
            "status": "disabled",
        }

    logger.info(f"Generating summary for crawl {crawl_id}")
    
    # TODO: Implement summary generation using LLM
    
    return {
        "crawl_id": crawl_id,
        "summary_generated": True
    }