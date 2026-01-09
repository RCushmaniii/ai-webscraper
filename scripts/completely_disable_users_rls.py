#!/usr/bin/env python3
"""Completely disable RLS on users table"""
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
print("COMPLETELY DISABLE USERS TABLE RLS")
print("="*70)

try:
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()

    # Drop ALL policies on users
    print("\n[1/3] Dropping ALL policies on users table...")
    cursor.execute("DROP POLICY IF EXISTS \"Users can view own profile\" ON users")
    cursor.execute("DROP POLICY IF EXISTS \"Users can update own profile\" ON users")
    cursor.execute("DROP POLICY IF EXISTS \"Admins can view all users\" ON users")
    cursor.execute("DROP POLICY IF EXISTS \"Users can insert their own data\" ON users")
    cursor.execute("DROP POLICY IF EXISTS \"Users can update their own data\" ON users")
    cursor.execute("DROP POLICY IF EXISTS \"Users can view their own data\" ON users")
    print("[OK] All policies dropped")

    # Disable RLS
    print("\n[2/3] Disabling RLS on users table...")
    cursor.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    print("[OK] RLS disabled")

    # Verify
    print("\n[3/3] Verifying...")
    cursor.execute("""
        SELECT tablename, rowsecurity
        FROM pg_tables
        WHERE tablename = 'users' AND schemaname = 'public'
    """)
    result = cursor.fetchone()
    if result:
        rls_status = "ENABLED" if result[1] else "DISABLED"
        print(f"[OK] users table: RLS {rls_status}")

    cursor.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename = 'users'")
    policy_count = cursor.fetchone()[0]
    print(f"[OK] Policies on users: {policy_count}")

    cursor.close()
    conn.close()

    print("\n" + "="*70)
    print("USERS RLS COMPLETELY DISABLED!")
    print("="*70)
    print("\nNow test auth again.")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)