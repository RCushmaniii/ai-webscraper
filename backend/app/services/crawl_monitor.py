"""
Background service to monitor and fix stale crawls
"""
from datetime import datetime, timezone, timedelta
from app.db.supabase import supabase_client
import logging

logger = logging.getLogger(__name__)

# Timeout thresholds (in minutes)
RUNNING_TIMEOUT = 30
QUEUED_TIMEOUT = 60
PENDING_TIMEOUT = 60

def check_and_fix_stale_crawls():
    """
    Check for crawls stuck in running/queued/pending state and mark them as failed.
    This should be called periodically (e.g., every 5-10 minutes).
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Get all non-terminal crawls
        response = supabase_client.table('crawls').select('*').in_('status', ['running', 'queued', 'pending']).execute()
        
        if not response.data:
            return
        
        stale_count = 0
        
        for crawl in response.data:
            created_at = datetime.fromisoformat(crawl['created_at'].replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(crawl['updated_at'].replace('Z', '+00:00'))
            
            last_activity = max(created_at, updated_at)
            time_elapsed = (now - last_activity).total_seconds() / 60
            
            status = crawl['status']
            timeout = RUNNING_TIMEOUT if status == 'running' else (QUEUED_TIMEOUT if status == 'queued' else PENDING_TIMEOUT)
            
            if time_elapsed > timeout:
                logger.warning(f"Marking stale crawl as failed: {crawl['id']} ({crawl['name']}) - {time_elapsed:.1f} minutes in {status} state")
                
                supabase_client.table('crawls').update({
                    'status': 'failed',
                    'error': f'Crawl timed out after {time_elapsed:.1f} minutes in {status} state',
                    'updated_at': now.isoformat()
                }).eq('id', crawl['id']).execute()
                
                stale_count += 1
        
        if stale_count > 0:
            logger.info(f"Fixed {stale_count} stale crawls")
            
    except Exception as e:
        logger.error(f"Error checking stale crawls: {e}")
