"""
Fix stale crawls that have been stuck in running/pending/queued status for too long
"""
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))

from app.db.supabase import supabase_client

# Define timeout thresholds (in minutes)
RUNNING_TIMEOUT = 30  # If a crawl has been "running" for more than 30 minutes, mark as failed
QUEUED_TIMEOUT = 60   # If a crawl has been "queued" for more than 60 minutes, mark as failed
PENDING_TIMEOUT = 60  # If a crawl has been "pending" for more than 60 minutes, mark as failed

def fix_stale_crawls():
    """Find and fix crawls that have been stuck in a running state for too long"""
    
    now = datetime.utcnow()
    
    # Get all crawls that are not in a terminal state
    response = supabase_client.table('crawls').select('*').in_('status', ['running', 'queued', 'pending']).execute()
    
    if not response.data:
        print("No active crawls found.")
        return
    
    stale_crawls = []
    
    for crawl in response.data:
        created_at = datetime.fromisoformat(crawl['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(crawl['updated_at'].replace('Z', '+00:00'))
        
        # Use the most recent timestamp
        last_activity = max(created_at, updated_at)
        time_elapsed = (now - last_activity.replace(tzinfo=None)).total_seconds() / 60  # in minutes
        
        status = crawl['status']
        timeout = RUNNING_TIMEOUT if status == 'running' else (QUEUED_TIMEOUT if status == 'queued' else PENDING_TIMEOUT)
        
        if time_elapsed > timeout:
            stale_crawls.append({
                'id': crawl['id'],
                'name': crawl['name'],
                'status': status,
                'created_at': created_at,
                'time_elapsed': time_elapsed
            })
    
    if not stale_crawls:
        print("No stale crawls found.")
        return
    
    print(f"\n=== FOUND {len(stale_crawls)} STALE CRAWLS ===\n")
    
    for crawl in stale_crawls:
        print(f"Crawl: {crawl['name']}")
        print(f"  ID: {crawl['id']}")
        print(f"  Status: {crawl['status']}")
        print(f"  Created: {crawl['created_at']}")
        print(f"  Time Elapsed: {crawl['time_elapsed']:.1f} minutes")
        print(f"  Action: Marking as failed\n")
        
        # Update the crawl to failed status
        update_response = supabase_client.table('crawls').update({
            'status': 'failed',
            'error': f'Crawl timed out after {crawl["time_elapsed"]:.1f} minutes in {crawl["status"]} state',
            'updated_at': now.isoformat()
        }).eq('id', crawl['id']).execute()
        
        if hasattr(update_response, 'error') and update_response.error:
            print(f"  ERROR updating crawl: {update_response.error}")
        else:
            print(f"  ✓ Successfully marked as failed")
    
    print(f"\n=== FIXED {len(stale_crawls)} STALE CRAWLS ===")

if __name__ == '__main__':
    fix_stale_crawls()
