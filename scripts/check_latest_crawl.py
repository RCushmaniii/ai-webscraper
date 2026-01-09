"""Check the latest crawl for error details"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import settings
from supabase import create_client

# Use service role to bypass RLS
supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

# Get latest crawl
result = supabase_client.table("crawls").select("*").order("created_at", desc=True).limit(1).execute()

if result.data:
    crawl = result.data[0]
    print("=== LATEST CRAWL ===")
    print(f"ID: {crawl['id']}")
    print(f"URL: {crawl['url']}")
    print(f"Status: {crawl['status']}")
    print(f"Pages Crawled: {crawl.get('pages_crawled', 0)}")
    print(f"Error: {crawl.get('error', 'No error message')}")
    print(f"Created: {crawl['created_at']}")

    # Check for pages
    pages_result = supabase_client.table("pages").select("*").eq("crawl_id", crawl['id']).execute()
    print(f"\nPages found: {len(pages_result.data) if pages_result.data else 0}")

    if pages_result.data:
        for page in pages_result.data:
            print(f"  - {page['url']}: {page.get('title', 'No title')} (status: {page.get('status_code', '?')})")

    # Check for issues
    issues_result = supabase_client.table("issues").select("*").eq("crawl_id", crawl['id']).execute()
    print(f"\nIssues found: {len(issues_result.data) if issues_result.data else 0}")

    if issues_result.data:
        for issue in issues_result.data[:5]:  # Show first 5
            print(f"  - [{issue.get('severity', '?')}] {issue.get('message', 'No message')}")
else:
    print("No crawls found")