#!/usr/bin/env python3
"""Check database data and RLS policies"""
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

print("="*70)
print("DATABASE DATA CHECK")
print("="*70)

try:
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Check users
    print("\n[1/5] Checking users table...")
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Total users: {user_count}")

    if user_count > 0:
        cursor.execute("SELECT id, email, is_admin FROM users LIMIT 3")
        for row in cursor.fetchall():
            print(f"  - User: {row[1]} (admin={row[2]})")

    # Check crawls
    print("\n[2/5] Checking crawls table...")
    cursor.execute("SELECT COUNT(*) FROM crawls")
    crawl_count = cursor.fetchone()[0]
    print(f"Total crawls: {crawl_count}")

    if crawl_count > 0:
        cursor.execute("SELECT id, user_id, url, status, created_at FROM crawls ORDER BY created_at DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - Crawl: {row[2][:50]} (status={row[3]}, user={row[1]})")

    # Check pages
    print("\n[3/5] Checking pages table...")
    cursor.execute("SELECT COUNT(*) FROM pages")
    page_count = cursor.fetchone()[0]
    print(f"Total pages: {page_count}")

    # Check RLS on crawls
    print("\n[4/5] Checking RLS policies on crawls...")
    cursor.execute("""
        SELECT tablename, policyname, cmd, qual
        FROM pg_policies
        WHERE tablename = 'crawls'
    """)
    policies = cursor.fetchall()
    print(f"Found {len(policies)} RLS policies on crawls:")
    for p in policies:
        print(f"  - {p[1]} ({p[2]})")

    # Check if RLS is enabled
    print("\n[5/5] Checking RLS status...")
    cursor.execute("""
        SELECT schemaname, tablename, rowsecurity
        FROM pg_tables
        WHERE tablename IN ('users', 'crawls', 'pages', 'batches')
    """)
    for row in cursor.fetchall():
        rls_status = "ENABLED" if row[2] else "DISABLED"
        print(f"  - {row[1]}: RLS {rls_status}")

    cursor.close()
    conn.close()

    print("\n" + "="*70)
    print("DATA CHECK COMPLETE")
    print("="*70)

    if crawl_count == 0:
        print("\n⚠️  NO CRAWLS IN DATABASE!")
        print("This is why dashboard shows 0.")
        print("You need to create a crawl first.")
    elif user_count == 0:
        print("\n⚠️  NO USERS IN DATABASE!")
        print("Auth won't work without users.")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)