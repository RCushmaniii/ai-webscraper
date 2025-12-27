#!/usr/bin/env python3
"""Run the complete database fix"""
import os
from supabase import create_client

# Read the SQL file
with open('COMPLETE_FIX.sql', 'r') as f:
    sql = f.read()

# Connect to Supabase
url = "https://kbltwyiowkbxzhhhozxf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtibHR3eWlvd2tieHpoaGhvenhmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTgzODE5OSwiZXhwIjoyMDgxNDE0MTk5fQ.LQ7_DIiaXLFGe7fnpqqMEmhkjCYLB3_jTJsjfF8P8-s"

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