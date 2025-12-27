#!/usr/bin/env python3
"""Query the check constraint on crawls.status"""
from supabase import create_client

url = "https://kbltwyiowkbxzhhhozxf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtibHR3eWlvd2tieHpoaGhvenhmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTgzODE5OSwiZXhwIjoyMDgxNDE0MTk5fQ.LQ7_DIiaXLFGe7fnpqqMEmhkjCYLB3_jTJsjfF8P8-s"

supabase = create_client(url, key)

# Query constraint definition
query = """
SELECT
  conname AS constraint_name,
  pg_get_constraintdef(c.oid) AS constraint_definition
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE conrelid = 'public.crawls'::regclass
  AND contype = 'c'
"""

try:
    # Use PostgREST to query pg_catalog (may not work, but worth trying)
    # If this fails, we'll use a different approach
    result = supabase.table('pg_constraint').select('*').execute()
    print("Direct query result:", result)
except Exception as e:
    print(f"Direct query failed: {e}")
    print("\nTrying RPC approach...")

    # Try using raw SQL via rpc if available
    try:
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        print("RPC result:", result)
    except Exception as e2:
        print(f"RPC also failed: {e2}")
        print("\nManual check needed - checking crawls table directly...")

        # As fallback, let's just check if we can query crawls table
        # and see what we can infer
        try:
            crawls = supabase.table('crawls').select('status').limit(5).execute()
            print("\nExisting crawl statuses in database:")
            for crawl in crawls.data:
                print(f"  - {crawl.get('status')}")
        except Exception as e3:
            print(f"Even basic query failed: {e3}")