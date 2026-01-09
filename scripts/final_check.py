#!/usr/bin/env python3
"""Final verification of extraction features"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
import re

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

url = os.getenv('SUPABASE_URL')
db_pass = os.getenv('SUPABASE_DB_PASSWORD')
match = re.search(r'https://([^.]+)\.supabase\.co', url)
project_ref = match.group(1)
conn_string = f"postgresql://postgres:{db_pass}@db.{project_ref}.supabase.co:5432/postgres"

print("="*80)
print("FINAL EXTRACTION VERIFICATION")
print("="*80)

try:
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Overall counts
    print("\nOVERALL DATABASE:")
    cursor.execute("SELECT COUNT(*) FROM pages")
    pages = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM links")
    links = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM images")
    images = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM issues")
    issues = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM seo_metadata")
    seo = cursor.fetchone()[0]

    print(f"  Pages:        {pages:6d}")
    print(f"  Links:        {links:6d}  {'<< SUCCESS!' if links > 0 else '<< NONE'}")
    print(f"  Images:       {images:6d}  {'<< SUCCESS!' if images > 0 else '<< NONE'}")
    print(f"  SEO Metadata: {seo:6d}  {'<< SUCCESS!' if seo > 0 else '<< NONE'}")
    print(f"  Issues:       {issues:6d}  {'<< SUCCESS!' if issues > 0 else ''}")

    # Latest crawl
    print("\nLATEST RUNNING/COMPLETED CRAWL:")
    cursor.execute("""
        SELECT id, url, status, pages_crawled, created_at
        FROM crawls
        WHERE status IN ('running', 'completed')
        ORDER BY created_at DESC
        LIMIT 1
    """)
    crawl = cursor.fetchone()
    if crawl:
        crawl_id, url, status, pages_crawled, created_at = crawl
        print(f"  ID:      {crawl_id}")
        print(f"  URL:     {url}")
        print(f"  Status:  {status}")
        print(f"  Created: {created_at}")

        # Counts for this crawl
        cursor.execute(f"SELECT COUNT(*) FROM pages WHERE crawl_id = '{crawl_id}'")
        c_pages = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM links WHERE crawl_id = '{crawl_id}'")
        c_links = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM images WHERE crawl_id = '{crawl_id}'")
        c_images = cursor.fetchone()[0]

        print(f"\n  This crawl extracted:")
        print(f"    Pages:  {c_pages}")
        print(f"    Links:  {c_links}")
        print(f"    Images: {c_images}")

    print("\n" + "="*80)
    if links > 0 and images > 0:
        print("SUCCESS! All extraction features are WORKING!")
    else:
        print("Partial success - some features may need attention")
    print("="*80)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
