"""
Direct test of the crawl functionality to verify it works end-to-end
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.crawler import Crawler
from app.db.supabase import supabase_client
import uuid
from datetime import datetime

# Create a test crawl record
crawl_id = str(uuid.uuid4())
test_url = "https://example.com"

print(f"Creating test crawl: {crawl_id}")
print(f"URL: {test_url}")

# Insert crawl record
crawl_data = {
    "id": crawl_id,
    "user_id": "e96591f3-8f18-4063-924d-a6d46f0608d9",  # Your user ID
    "url": test_url,
    "name": "Direct Test Crawl",
    "max_depth": 1,
    "max_pages": 5,
    "respect_robots_txt": True,
    "follow_external_links": False,
    "js_rendering": False,
    "rate_limit": 2,
    "user_agent": "AI WebScraper Bot",
    "concurrency": 5,
    "status": "running",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
}

result = supabase_client.table("crawls").insert(crawl_data).execute()
print(f"Crawl record created: {result.data}")

# Create crawler and run
print("\nStarting crawl...")
from app.models.models import Crawl

# Create Crawl model from the data
crawl_model = Crawl(**crawl_data)
crawler = Crawler(crawl=crawl_model)

try:
    import asyncio
    asyncio.run(crawler.start())
    print("\nCrawl completed!")
    
    # Check results
    pages = supabase_client.table('pages').select('id, url, title, status_code').eq('crawl_id', crawl_id).execute()
    print(f"\nPages crawled: {len(pages.data)}")
    for page in pages.data:
        print(f"  - {page['url']}")
        print(f"    Title: {page.get('title', 'No title')}")
        print(f"    Status: {page.get('status_code', 'Unknown')}")
    
    # Update crawl status
    supabase_client.table("crawls").update({"status": "completed", "updated_at": datetime.now().isoformat()}).eq("id", crawl_id).execute()
    print("\nCrawl marked as completed")
    
except Exception as e:
    print(f"\nError during crawl: {e}")
    import traceback
    traceback.print_exc()
    supabase_client.table("crawls").update({"status": "failed", "updated_at": datetime.now().isoformat()}).eq("id", crawl_id).execute()
