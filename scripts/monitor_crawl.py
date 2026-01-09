#!/usr/bin/env python3
"""Real-time crawl monitoring with debugging"""
import os
import sys
import time
from dotenv import load_dotenv
import psycopg2
import re
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

url = os.getenv('SUPABASE_URL')
db_pass = os.getenv('SUPABASE_DB_PASSWORD')
match = re.search(r'https://([^.]+)\.supabase\.co', url)
project_ref = match.group(1)
conn_string = f"postgresql://postgres:{db_pass}@db.{project_ref}.supabase.co:5432/postgres"

def get_latest_crawl():
    """Get the most recent crawl"""
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, url, status, pages_crawled, created_at, updated_at
        FROM crawls
        ORDER BY created_at DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_crawl_stats(crawl_id):
    """Get comprehensive stats for a crawl"""
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    stats = {}

    # Pages
    cursor.execute(f"SELECT COUNT(*) FROM pages WHERE crawl_id = '{crawl_id}'")
    stats['pages'] = cursor.fetchone()[0]

    # Links
    cursor.execute(f"SELECT COUNT(*) FROM links WHERE crawl_id = '{crawl_id}'")
    stats['links'] = cursor.fetchone()[0]

    # Images
    cursor.execute(f"SELECT COUNT(*) FROM images WHERE crawl_id = '{crawl_id}'")
    stats['images'] = cursor.fetchone()[0]

    # Issues
    cursor.execute(f"SELECT COUNT(*) FROM issues WHERE crawl_id = '{crawl_id}'")
    stats['issues'] = cursor.fetchone()[0]

    # SEO Metadata
    cursor.execute(f"SELECT COUNT(*) FROM seo_metadata sm JOIN pages p ON sm.page_id = p.id WHERE p.crawl_id = '{crawl_id}'")
    stats['seo_metadata'] = cursor.fetchone()[0]

    # Latest page
    cursor.execute(f"""
        SELECT url, title, status_code
        FROM pages
        WHERE crawl_id = '{crawl_id}'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    latest = cursor.fetchone()
    if latest:
        stats['latest_page_url'] = latest[0][:60]
        stats['latest_page_title'] = latest[1][:40] if latest[1] else 'No title'
        stats['latest_page_status'] = latest[2]

    cursor.close()
    conn.close()
    return stats

def monitor_crawl(crawl_id, duration=60):
    """Monitor a crawl for specified duration"""
    print(f"\n{'='*80}")
    print(f"MONITORING CRAWL: {crawl_id}")
    print(f"{'='*80}")

    start_time = time.time()
    iteration = 0

    try:
        while time.time() - start_time < duration:
            iteration += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iteration {iteration}")
            print("-" * 80)

            # Get crawl status
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT status, pages_crawled, error
                FROM crawls
                WHERE id = '{crawl_id}'
            """)
            crawl_info = cursor.fetchone()
            cursor.close()
            conn.close()

            if not crawl_info:
                print("❌ Crawl not found!")
                break

            status, pages_crawled, error = crawl_info
            print(f"Status: {status.upper()}")
            print(f"Pages Crawled: {pages_crawled}")

            if error:
                print(f"WARNING - ERROR: {error[:100]}")

            # Get detailed stats
            stats = get_crawl_stats(crawl_id)

            print(f"\nDATABASE STATS:")
            print(f"  Pages:        {stats['pages']:4d}")
            print(f"  Links:        {stats['links']:4d}")
            print(f"  Images:       {stats['images']:4d}")
            print(f"  Issues:       {stats['issues']:4d}")
            print(f"  SEO Metadata: {stats['seo_metadata']:4d}")

            if 'latest_page_url' in stats:
                print(f"\nLatest Page:")
                print(f"  URL:    {stats['latest_page_url']}")
                print(f"  Title:  {stats['latest_page_title']}")
                print(f"  Status: {stats['latest_page_status']}")

            # Check for success indicators
            if stats['links'] > 0:
                print("\n[SUCCESS] Links are being saved!")
            if stats['images'] > 0:
                print("[SUCCESS] Images are being saved!")
            if stats['issues'] > 0:
                print("[SUCCESS] Issues are being saved!")

            # Stop if crawl completed or failed
            if status in ['completed', 'failed']:
                print(f"\n{'='*80}")
                print(f"Crawl {status.upper()}")
                print(f"{'='*80}")
                print(f"\nFINAL STATS:")
                print(f"  Pages:        {stats['pages']}")
                print(f"  Links:        {stats['links']}")
                print(f"  Images:       {stats['images']}")
                print(f"  Issues:       {stats['issues']}")
                print(f"  SEO Metadata: {stats['seo_metadata']}")

                if stats['links'] > 0 and stats['images'] > 0 and stats['issues'] > 0:
                    print(f"\n*** COMPLETE SUCCESS! All extraction working! ***")
                elif stats['pages'] > 0:
                    if stats['links'] == 0:
                        print(f"\nWARNING: No links saved!")
                    if stats['images'] == 0:
                        print(f"\nWARNING: No images saved!")
                    if stats['issues'] == 0:
                        print(f"\nWARNING: No issues saved!")
                break

            time.sleep(5)  # Check every 5 seconds

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*80)
    print("REAL-TIME CRAWL MONITOR")
    print("="*80)

    if len(sys.argv) > 1:
        crawl_id = sys.argv[1]
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    else:
        print("\nGetting latest crawl...")
        latest = get_latest_crawl()
        if not latest:
            print("No crawls found. Please start a crawl first.")
            sys.exit(1)

        crawl_id, url, status, pages_crawled, created_at, updated_at = latest
        print(f"\nLatest Crawl:")
        print(f"  ID:      {crawl_id}")
        print(f"  URL:     {url}")
        print(f"  Status:  {status}")
        print(f"  Pages:   {pages_crawled}")
        print(f"  Created: {created_at}")

        duration = 120  # 2 minutes

    print(f"\nMonitoring for {duration} seconds...")
    monitor_crawl(crawl_id, duration)
