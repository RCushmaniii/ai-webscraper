import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.supabase import supabase_client
import json

# Get recent crawls
print("=== RECENT CRAWLS ===")
crawls = supabase_client.table('crawls').select('id, name, url, status, created_at').order('created_at', desc=True).limit(5).execute()
for crawl in crawls.data:
    print(f"\nCrawl: {crawl['name']}")
    print(f"  ID: {crawl['id']}")
    print(f"  URL: {crawl['url']}")
    print(f"  Status: {crawl['status']}")
    print(f"  Created: {crawl['created_at']}")
    
    # Check for pages
    pages = supabase_client.table('pages').select('id, url, title').eq('crawl_id', crawl['id']).execute()
    print(f"  Pages found: {len(pages.data)}")
    if pages.data:
        for page in pages.data[:3]:
            print(f"    - {page['url']}: {page.get('title', 'No title')}")

print("\n=== TOTAL PAGES IN DATABASE ===")
all_pages = supabase_client.table('pages').select('id', count='exact').execute()
print(f"Total pages: {all_pages.count}")
