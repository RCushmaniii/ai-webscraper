import logging
import asyncio
from celery import Celery
from typing import Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
import ssl

from app.core.config import settings
from app.models.models import Crawl, CrawlCreate
from app.services.crawler import Crawler
from app.db.supabase import supabase_client

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

# Configure logging
logger = logging.getLogger(__name__)

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
        # 1. Fetch crawl data from Supabase
        response = supabase_client.table("crawls").select("*").eq("id", crawl_id).single().execute()

        if response.data is None:
            logger.error(f"Crawl with id {crawl_id} not found.")
            raise ValueError(f"Crawl not found: {crawl_id}")

        # 2. Instantiate Crawl model
        crawl_model = Crawl(**response.data)

        # 3. Instantiate Crawler with the model
        crawler = Crawler(crawl=crawl_model)

        # 4. Run the crawl (asynchronously)
        asyncio.run(crawler.start())

        progress = crawler.get_progress()

        # 5. Update crawl status and final metrics in database
        final_update = {
            "status": "completed",
            "pages_crawled": progress.pages_crawled,
            "total_links": len(crawler.visited_urls) + len(crawler.url_queue),
            "completed_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        supabase_client.table("crawls").update(final_update).eq("id", crawl_id).execute()

        # 6. Run comprehensive SEO audit
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
        supabase_client.table("crawls").update({"status": "failed", "error": str(e)}).eq("id", crawl_id).execute()
        return {
            "crawl_id": crawl_id,
            "status": "failed",
            "error": str(e)
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
            supabase_client.table("crawls").insert(crawl_data).execute()
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