"""
Inspect what data is actually stored for a crawled page
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.supabase import supabase_client
import json

# Get the most recent page
pages = supabase_client.table('pages').select('*').order('created_at', desc=True).limit(1).execute()

if pages.data:
    page = pages.data[0]
    print("=== PAGE DATA ===")
    print(json.dumps(page, indent=2, default=str))
    
    print("\n=== WHAT'S STORED ===")
    print(f"Title: {page.get('title')}")
    print(f"URL: {page.get('url')}")
    print(f"Status Code: {page.get('status_code')}")
    print(f"Word Count: {page.get('word_count')}")
    print(f"Text Excerpt (first 500 chars): {page.get('text_excerpt', '')[:500]}")
    print(f"HTML Storage Path: {page.get('html_storage_path')}")
    print(f"Content Hash: {page.get('content_hash')}")
    
    # Check for SEO metadata
    print("\n=== SEO METADATA ===")
    seo = supabase_client.table('seo_metadata').select('*').eq('page_id', page['id']).execute()
    if seo.data:
        print(json.dumps(seo.data[0], indent=2, default=str))
    else:
        print("No SEO metadata found")
else:
    print("No pages found in database")
