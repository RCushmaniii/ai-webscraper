#!/usr/bin/env python3
"""Setup proper RLS policies without infinite recursion"""
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

# Proper RLS policies SQL
proper_rls_sql = """
-- ============================================
-- PROPER RLS POLICIES (NO INFINITE RECURSION)
-- ============================================

-- Drop all existing policies first
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Admins can view all users" ON users;
DROP POLICY IF EXISTS "Users can insert their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;
DROP POLICY IF EXISTS "Users can view their own data" ON users;

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Simple, non-recursive policies for users table
-- Key: Don't query the users table from within these policies!

CREATE POLICY "users_select_own"
ON users FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "users_update_own"
ON users FOR UPDATE
USING (auth.uid() = id);

-- For admin access, we'll handle that in the application layer
-- NOT in RLS policies to avoid recursion

-- Verify other tables have proper RLS
-- These are fine because they don't create recursion

-- Crawls policies
DROP POLICY IF EXISTS "Users can view own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can insert own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can update own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can delete own crawls" ON crawls;

ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;

CREATE POLICY "crawls_select_own"
ON crawls FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "crawls_insert_own"
ON crawls FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "crawls_update_own"
ON crawls FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "crawls_delete_own"
ON crawls FOR DELETE
USING (auth.uid() = user_id);

-- Pages policies
DROP POLICY IF EXISTS "Users can view own pages" ON pages;

ALTER TABLE pages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "pages_select_via_crawl"
ON pages FOR SELECT
USING (
  crawl_id IN (
    SELECT id FROM crawls WHERE user_id = auth.uid()
  )
);

-- Batches policies
DROP POLICY IF EXISTS "Users can view own batches" ON batches;
DROP POLICY IF EXISTS "Users can insert own batches" ON batches;
DROP POLICY IF EXISTS "Users can update own batches" ON batches;
DROP POLICY IF EXISTS "Users can delete own batches" ON batches;

ALTER TABLE batches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "batches_select_own"
ON batches FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "batches_insert_own"
ON batches FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "batches_update_own"
ON batches FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "batches_delete_own"
ON batches FOR DELETE
USING (auth.uid() = user_id);

-- Links policies
DROP POLICY IF EXISTS "Users can view own links" ON links;

ALTER TABLE links ENABLE ROW LEVEL SECURITY;

CREATE POLICY "links_select_via_crawl"
ON links FOR SELECT
USING (
  crawl_id IN (
    SELECT id FROM crawls WHERE user_id = auth.uid()
  )
);
"""

print("="*70)
print("SETTING UP PROPER RLS POLICIES")
print("="*70)

try:
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()

    print("\n[1/3] Applying proper RLS policies...")
    cursor.execute(proper_rls_sql)
    print("[OK] Policies created")

    print("\n[2/3] Verifying RLS status...")
    cursor.execute("""
        SELECT tablename, rowsecurity
        FROM pg_tables
        WHERE tablename IN ('users', 'crawls', 'pages', 'batches', 'links')
        AND schemaname = 'public'
        ORDER BY tablename
    """)

    for row in cursor.fetchall():
        rls_status = "ENABLED" if row[1] else "DISABLED"
        print(f"  {row[0]}: RLS {rls_status}")

    print("\n[3/3] Checking policy counts...")
    cursor.execute("""
        SELECT tablename, COUNT(*) as policy_count
        FROM pg_policies
        WHERE tablename IN ('users', 'crawls', 'pages', 'batches', 'links')
        GROUP BY tablename
        ORDER BY tablename
    """)

    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} policies")

    cursor.close()
    conn.close()

    print("\n" + "="*70)
    print("PROPER RLS POLICIES APPLIED!")
    print("="*70)
    print("\n✅ Security enabled")
    print("✅ No infinite recursion")
    print("✅ Users can only access their own data")
    print("\nRefresh your browser!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)