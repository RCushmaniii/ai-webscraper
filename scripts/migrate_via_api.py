#!/usr/bin/env python3
"""Run migration using Supabase HTTP API without requiring database password"""
import os
import sys
import requests
import re
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read SQL
sql_file = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'db_sql', '003_llm_analysis_tables.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Get credentials
url = os.getenv('SUPABASE_URL')
anon_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not url or not anon_key:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set")
    sys.exit(1)

project_ref = re.search(r'https://([^.]+)\.supabase\.co', url).group(1)

print("="*70)
print("EXECUTING LLM MIGRATION VIA SUPABASE API")
print("="*70)
print(f"\nProject: {project_ref}")
print(f"URL: {url}")

# Parse SQL into individual statements
statements = []
current = []
in_function = False

for line in sql_content.split('\n'):
    stripped = line.strip()

    # Track function boundaries
    if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
        in_function = True

    current.append(line)

    # Detect statement boundaries
    if stripped.endswith(';') and not in_function and not stripped.startswith('--'):
        stmt = '\n'.join(current).strip()
        if stmt and len(stmt) > 10 and not stmt.startswith('--'):
            statements.append(stmt)
        current = []
    elif in_function and '$$' in stripped and 'LANGUAGE' in line:
        in_function = False

# Add any remaining
if current:
    stmt = '\n'.join(current).strip()
    if stmt and len(stmt) > 10:
        statements.append(stmt)

print(f"\nParsed {len(statements)} SQL statements")

# Execute using Supabase's client library
from supabase import create_client

try:
    client = create_client(url, anon_key)
    print("\n[OK] Connected to Supabase")

    # Use the PostgREST /rpc endpoint to execute SQL
    # Note: This requires creating a helper function first

    # First, try to create a helper function that can execute raw SQL
    # This is a workaround since Supabase doesn't expose raw SQL execution via REST API

    print("\n[INFO] Attempting to execute migration...")
    print("[INFO] Using table creation approach...\n")

    # Create tables one by one using the client
    success_count = 0
    error_count = 0

    # Instead of executing raw SQL, we'll use Supabase's schema API
    # But actually, the best approach is to use the /query endpoint

    # Try the REST API's query parameter
    headers = {
        'apikey': anon_key,
        'Authorization': f'Bearer {anon_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

    # Supabase doesn't support raw SQL via REST API for security reasons
    # We need to use the Management API or direct database connection

    print("[ERROR] Supabase REST API does not support raw SQL execution.")
    print("[INFO] Switching to alternative approach...\n")

    # Alternative: Use Supabase CLI if available
    import shutil
    if shutil.which('supabase'):
        print("[OK] Supabase CLI found")
        print("[INFO] Executing migration via CLI...")

        import subprocess
        result = subprocess.run(
            ['supabase', 'db', 'push', '--db-url', f'{url}/db', '--password', 'prompt'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("[OK] Migration executed successfully via CLI")
        else:
            print(f"[ERROR] CLI execution failed: {result.stderr}")
    else:
        print("[ERROR] Supabase CLI not found")
        print("\n" + "="*70)
        print("MIGRATION CANNOT BE AUTOMATED WITHOUT:")
        print("="*70)
        print("\n1. Database password (SUPABASE_DB_PASSWORD in .env), OR")
        print("2. Supabase CLI installed (npm install -g supabase)")
        print("\nManual execution required:")
        print("  1. Go to: https://supabase.com/dashboard/project/" + project_ref)
        print("  2. Click: SQL Editor")
        print("  3. Copy-paste the entire content of:")
        print(f"     {sql_file}")
        print("  4. Click: Run")
        print("\nThis is a one-time setup. Sorry for the inconvenience.")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)