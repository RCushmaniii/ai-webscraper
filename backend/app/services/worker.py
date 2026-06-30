import logging
import asyncio
from typing import Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
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

# Create service role client (bypasses RLS for background tasks)
service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

logger.info("Service client initialized")


async def crawl_site(crawl_id: str) -> Dict[str, Any]:
    """
    Background task to crawl a site.

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
                logger.warning(f"Single fetch failed, checking if crawl exists at all...")
                check_response = service_client.table("crawls").select("id").eq("id", crawl_id).execute()

                if check_response.data and len(check_response.data) > 0:
                    logger.error(f"Crawl {crawl_id} exists but service role can't access it - RLS issue!")
                    raise ValueError(f"RLS blocking service role access to crawl {crawl_id}. Check RLS policies.")
                else:
                    logger.error(f"Crawl {crawl_id} does not exist in database (may have been deleted).")
                    raise ValueError(f"Crawl not found: {crawl_id}")
            else:
                logger.error(f"Unexpected error fetching crawl: {error_msg}")
                raise

        if response.data is None:
            logger.error(f"Crawl with id {crawl_id} not found (response.data is None).")
            raise ValueError(f"Crawl not found: {crawl_id}")

        # 2. Instantiate Crawl model
        crawl_model = Crawl(**response.data)

        # 2.5. Mark crawl as running
        service_client.table("crawls").update({
            "status": "running",
            "updated_at": datetime.now().isoformat()
        }).eq("id", crawl_id).execute()

        logger.info(f"Starting crawler for {crawl_model.url}")

        # 3. Instantiate Crawler with the model and service client (bypasses RLS)
        crawler = Crawler(crawl=crawl_model, db_client=service_client)

        # 4. Run the crawl
        await crawler.start()

        # pages_crawled counts pages FETCHED; pages_saved counts pages actually
        # PERSISTED. They diverge when a DB insert fails (e.g. a missing column),
        # which previously produced a "completed" crawl with 0 viewable pages.
        pages_fetched = crawler.pages_crawled
        pages_saved = crawler.pages_saved
        pages_save_failed = crawler.pages_save_failed
        logger.info(
            f"Crawl finished for {crawl_id}. Fetched: {pages_fetched}, "
            f"saved: {pages_saved}, save-failed: {pages_save_failed}"
        )

        # 5. Update crawl status and final metrics in database.
        # Report the SAVED count as pages_crawled — that's what the user can
        # actually view. Never report "completed" when nothing persisted.
        now_iso = datetime.now().isoformat()
        if pages_saved == 0:
            if pages_fetched > 0:
                # Pages were fetched but none saved — a database/persistence
                # failure, not a crawl-reachability problem. Surface it loudly.
                error_msg = (
                    f"Crawl fetched {pages_fetched} page(s) but saved 0 to the "
                    f"database ({pages_save_failed} insert failure(s)). This is a "
                    f"persistence error (e.g. a schema mismatch) — check the "
                    f"backend logs. No viewable pages were stored."
                )
                logger.error(f"Crawl {crawl_id}: {pages_fetched} fetched, 0 saved - marking as failed")
            else:
                error_msg = (
                    "Crawl completed but no pages were successfully crawled. This "
                    "could be due to: robots.txt blocking, connection issues, or "
                    "invalid URL."
                )
                logger.warning(f"Crawl {crawl_id} completed with 0 pages - marking as failed")
            final_update = {
                "status": "failed",
                "pages_crawled": 0,
                "total_links": 0,
                "error": error_msg,
                "completed_at": now_iso,
                "updated_at": now_iso,
            }
        else:
            final_update = {
                "status": "completed",
                "pages_crawled": pages_saved,
                "total_links": len(crawler.visited_urls) + len(crawler.url_queue),
                "completed_at": now_iso,
                "updated_at": now_iso,
            }
            if pages_save_failed > 0:
                # Partial failure: the crawl is usable but incomplete. Keep it
                # "completed" (report/issue-detection still apply) but record a
                # visible warning so the missing pages aren't a silent loss.
                final_update["error"] = (
                    f"Partial save: {pages_save_failed} of {pages_fetched} fetched "
                    f"page(s) failed to persist and are missing from this crawl. "
                    f"Check the backend logs."
                )
                logger.warning(
                    f"Crawl {crawl_id} completed with partial save: "
                    f"{pages_saved} saved, {pages_save_failed} failed"
                )
            else:
                # Clean run — clear any stale error from a prior re-run attempt.
                final_update["error"] = None

        service_client.table("crawls").update(final_update).eq("id", crawl_id).execute()

        # 6. Run Phase 1 issue detection (only if pages were actually saved)
        if pages_saved > 0:
            try:
                from app.services.issue_detector import detect_and_store_issues
                issues_count = await detect_and_store_issues(UUID(crawl_id), db_client=service_client)
                logger.info(f"Detected and stored {issues_count} issues for crawl {crawl_id}")
            except Exception as issue_error:
                logger.error(f"Error detecting issues for {crawl_id}: {issue_error}", exc_info=True)

        # 7. Run comprehensive SEO audit (only if pages were actually saved)
        if settings.ENABLE_SEO_AUDIT and pages_saved > 0:
            try:
                from app.services.seo_auditor import SEOAuditor
                auditor = SEOAuditor(crawl_id)
                audit_results = await auditor.run_comprehensive_audit()
                logger.info(
                    f"Completed SEO audit for crawl {crawl_id} with score: {audit_results.get('overall_score', 0)}"
                )
            except Exception as audit_error:
                logger.error(f"Error running SEO audit for {crawl_id}: {audit_error}")

        return {
            "crawl_id": crawl_id,
            "status": final_update["status"],
            "pages_crawled": pages_saved,
            "pages_save_failed": pages_save_failed,
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
            "error": error_msg[:500],
            "completed_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).eq("id", crawl_id).execute()

        return {
            "crawl_id": crawl_id,
            "status": "failed",
            "error": error_msg
        }


async def batch_crawl(batch_id: str, user_id: str, site_urls: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task to crawl multiple sites in a batch.
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
            # Run each crawl as a background coroutine
            asyncio.create_task(crawl_site(str(crawl_id)))
            results["crawl_ids"].append(str(crawl_id))
        except Exception as e:
            logger.error(f"Failed to create or dispatch crawl for {url}: {e}")

    return results


async def generate_summary(crawl_id: str) -> Dict[str, Any]:
    """
    Background task to generate a summary for a completed crawl.
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
