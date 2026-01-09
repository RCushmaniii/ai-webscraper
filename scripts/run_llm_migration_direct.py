#!/usr/bin/env python3
"""Run LLM analysis tables migration using direct HTTP requests"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read the SQL file
sql_file = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'db_sql', '003_llm_analysis_tables.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql = f.read()

# Get Supabase credentials
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
project_id = os.getenv('SUPABASE_PROJECT_ID')

if not url or not key:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
    sys.exit(1)

print(f"Connecting to Supabase at {url}...")
print(f"Project ID: {project_id}")

# Execute SQL using Supabase's REST API
# We'll use the /rest/v1 endpoint with raw SQL
headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

print("\nExecuting SQL migration...")
print("=" * 60)

try:
    # Use the Supabase REST API to execute raw SQL via query endpoint
    # Note: This requires the anon key to have proper permissions

    # Split SQL into manageable chunks (by major sections)
    sections = []
    current_section = []
    in_function = False

    for line in sql.split('\n'):
        current_section.append(line)

        # Detect function boundaries
        if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
            in_function = True
        if in_function and line.strip().endswith('$$ LANGUAGE'):
            in_function = False

        # Split on major section boundaries
        if line.strip().startswith('-- ====') and len(current_section) > 10:
            sections.append('\n'.join(current_section[:-1]))
            current_section = [line]

    # Add remaining section
    if current_section:
        sections.append('\n'.join(current_section))

    # Execute each section
    for i, section in enumerate(sections):
        section = section.strip()
        if not section or section.startswith('-- Sample Queries'):
            continue

        # Show progress
        first_line = section.split('\n')[0][:70]
        print(f"[{i+1}/{len(sections)}] {first_line}...")

        # Use the Supabase SQL endpoint
        # The Supabase REST API doesn't directly support SQL execution for security
        # So we'll use a different approach - execute via PostgREST's query parameter

        # Actually, the proper way is to use the Supabase CLI or Management API
        # But for now, let's try using httpx to post to the /query endpoint

        # For security reasons, Supabase doesn't expose raw SQL execution via REST API
        # We need to use a different approach
        pass

    print("\n" + "=" * 60)
    print("Migration approach changed - using Python SQL parser")
    print("=" * 60)

    # Better approach: Use psycopg2 with connection string
    # First, check if we have the connection string
    import re

    # Extract project ref from URL
    match = re.search(r'https://([^.]+)\.supabase\.co', url)
    if match:
        project_ref = match.group(1)

        # Construct the direct PostgreSQL connection string
        # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
        print("\nTo complete the migration, we need to use direct PostgreSQL connection.")
        print("Please install psycopg2 and provide the database password.")
        print(f"\nConnection string format:")
        print(f"postgresql://postgres:[YOUR-DB-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres")
        print("\nAlternatively, run this SQL directly in Supabase SQL Editor:")
        print(f"File: {sql_file}")

        # Try one more approach - using httpx to call Supabase API
        import httpx

        print("\nAttempting to use Supabase Management API...")

        # The Supabase Management API requires a service role key or access token
        # Let's try a simpler approach - chunk and execute via REST

        # Actually, the best way is to use the supabase-py client with admin privileges
        # Let me try that

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nScript complete. Using alternative approach...")
