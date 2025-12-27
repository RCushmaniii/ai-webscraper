"""
Manually trigger a crawl task for testing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.worker import crawl_site

# Trigger one of the queued crawls
crawl_id = "c9c79b87-8aba-4a04-96d5-eff69d550bc8"  # Test Example from yesterday

print(f"Manually triggering crawl: {crawl_id}")
result = crawl_site.delay(crawl_id)
print(f"Task dispatched: {result.id}")
print(f"Task state: {result.state}")
print("\nCheck the Celery worker terminal for progress...")
