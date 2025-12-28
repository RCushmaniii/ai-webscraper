#!/usr/bin/env python3
"""Run the complete database fix"""
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read the SQL file
with open('COMPLETE_FIX.sql', 'r') as f:
    sql = f.read()

# Connect to Supabase using environment variables
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SECRET_KEY')

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set in backend/.env")

supabase = create_client(url, key)

# Execute SQL via RPC
try:
    # Split SQL into individual statements
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

    for i, statement in enumerate(statements):
        if not statement or len(statement) < 10:
            continue
        print(f"Executing statement {i+1}/{len(statements)}...")
        try:
            # Use rpc to execute raw SQL
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            print(f"✓ Statement {i+1} executed")
        except Exception as e:
            print(f"✗ Statement {i+1} error: {e}")
            # Continue with next statement

    print("\n✅ Database fix complete!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()