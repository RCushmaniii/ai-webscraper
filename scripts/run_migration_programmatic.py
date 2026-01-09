#!/usr/bin/env python3
"""Execute migration by creating tables programmatically using Supabase client"""
import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read SQL
sql_file = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'db_sql', '003_llm_analysis_tables.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

url = os.getenv('SUPABASE_URL')
anon_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

print("="*70)
print("EXECUTING MIGRATION VIA HTTP API")
print("="*70)

# Use Supabase's GraphQL-like query endpoint
# This is a hack but should work for DDL statements

headers = {
    'apikey': anon_key,
    'Authorization': f'Bearer {anon_key}',
    'Content-Type': 'application/json',
}

# Try to execute via the pg_net extension if available
# Or use the supabase-js SQL endpoint

# Actually, let's try using the REST API's query functionality
# Supabase exposes a /query endpoint for executing SQL

try:
    # Split SQL into individual statements
    statements = []
    current = []
    in_function = False

    for line in sql_content.split('\n'):
        stripped = line.strip()

        if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
            in_function = True

        current.append(line)

        if stripped.endswith(';') and not in_function and not stripped.startswith('--'):
            stmt = '\n'.join(current).strip()
            if stmt and len(stmt) > 10 and not stmt.startswith('--') and not stmt.startswith('/*'):
                statements.append(stmt)
            current = []
        elif in_function and '$$' in stripped and 'LANGUAGE' in line:
            in_function = False

    if current:
        stmt = '\n'.join(current).strip()
        if stmt and len(stmt) > 10:
            statements.append(stmt)

    print(f"Parsed {len(statements)} statements\n")

    # Use httpx to make requests
    import httpx

    client = httpx.Client(timeout=30.0)

    # Try the Supabase REST API's /rest/v1/rpc endpoint
    # We need to call a stored procedure that executes SQL

    # First, check if we can create a helper function
    helper_sql = """
    CREATE OR REPLACE FUNCTION execute_sql(query text)
    RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        EXECUTE query;
    END;
    $$;
    """

    # Try to create the helper via HTTP POST to /rest/v1/rpc/exec
    # Actually, this won't work either without permissions

    # Let me try a different approach - use the PostgREST admin API
    # The issue is we need elevated privileges

    print("[INFO] Attempting direct SQL execution via REST API...")

    # Check if we have access to create extensions
    test_url = f"{url}/rest/v1/rpc/version"
    response = client.get(test_url, headers=headers)
    print(f"API Status: {response.status_code}")

    if response.status_code == 404:
        print("[ERROR] Cannot access database functions via REST API")
        print("[INFO] This requires either:")
        print("  1. Service role key (not anon key)")
        print("  2. Database password for direct connection")
        print("  3. Supabase CLI with proper configuration")
        print("\nTrying alternative: Supabase Management API...")

        # Try using httpx to POST to the management API
        # This requires a personal access token

        # Actually, let's just try to execute the SQL directly via psycopg2
        # We'll need to get the password from the user one time

        # Check if password exists in env
        db_pass = os.getenv('SUPABASE_DB_PASSWORD')

        if not db_pass:
            # Try to extract from SUPABASE_DB_URL if it exists
            db_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')

            if db_url and 'postgresql://' in db_url:
                import re
                match = re.search(r'postgresql://[^:]+:([^@]+)@', db_url)
                if match:
                    db_pass = match.group(1)
                    print("[OK] Found password in DATABASE_URL")

        if db_pass:
            print("[OK] Using database password from environment")

            # Install psycopg2 if needed
            try:
                import psycopg2
            except ImportError:
                print("[INFO] Installing psycopg2...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import psycopg2

            # Extract project ref
            import re
            match = re.search(r'https://([^.]+)\.supabase\.co', url)
            project_ref = match.group(1)

            # Use direct database connection (not pooler)
            conn_string = f"postgresql://postgres:{db_pass}@db.{project_ref}.supabase.co:5432/postgres"

            print(f"[INFO] Connecting to database...")

            try:
                conn = psycopg2.connect(conn_string)
                conn.autocommit = True
                cursor = conn.cursor()

                print("[OK] Connected successfully\n")
                print("Executing migration...\n")

                # Execute the full SQL
                cursor.execute(sql_content)

                # Verify tables
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('page_analysis', 'crawl_analysis', 'page_embeddings', 'llm_usage', 'image_analysis')
                    ORDER BY table_name
                """)

                tables = cursor.fetchall()

                cursor.close()
                conn.close()

                print("="*70)
                print("MIGRATION COMPLETED SUCCESSFULLY!")
                print("="*70)
                print(f"\nCreated {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table[0]}")

                print("\nLLM analysis features are now ready!")
                sys.exit(0)

            except Exception as e:
                print(f"[ERROR] Database connection failed: {e}")
                print("\nThe connection string format might be wrong.")
                print("Please add to backend/.env:")
                print("SUPABASE_DB_PASSWORD=<your-db-password>")
                sys.exit(1)
        else:
            print("\n[ERROR] Cannot execute migration automatically.")
            print("\nRequired: SUPABASE_DB_PASSWORD in backend/.env")
            print("\nTo get your password:")
            print("  1. Go to Supabase Dashboard")
            print("  2. Project Settings > Database")
            print("  3. Copy the database password")
            print("  4. Add to backend/.env: SUPABASE_DB_PASSWORD=<password>")
            print("  5. Re-run this script")
            sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)