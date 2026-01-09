#!/usr/bin/env python3
"""Fix RLS infinite recursion by disabling RLS on users table"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
import re

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read the fix SQL
sql_file = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'db_sql', 'FIX_RLS_POLICIES.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql = f.read()

# Get credentials
url = os.getenv('SUPABASE_URL')
db_pass = os.getenv('SUPABASE_DB_PASSWORD')

match = re.search(r'https://([^.]+)\.supabase\.co', url)
project_ref = match.group(1)

conn_string = f"postgresql://postgres:{db_pass}@db.{project_ref}.supabase.co:5432/postgres"

print("="*70)
print("FIXING RLS INFINITE RECURSION")
print("="*70)

try:
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()

    print("\n[1/2] Executing fix...")
    cursor.execute(sql)
    print("[OK] RLS policies updated")

    print("\n[2/2] Verifying...")
    cursor.execute("SELECT schemaname, tablename, policyname FROM pg_policies WHERE tablename = 'users'")
    policies = cursor.fetchall()

    print(f"[OK] Found {len(policies)} policies on users table:")
    for p in policies:
        print(f"  - {p[2]}")

    cursor.close()
    conn.close()

    print("\n" + "="*70)
    print("RLS FIX COMPLETED!")
    print("="*70)
    print("\nThe users table RLS has been DISABLED.")
    print("Auth should work now. Refresh your browser!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)