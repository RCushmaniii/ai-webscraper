#!/usr/bin/env python3
"""Run LLM analysis tables migration"""
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read the SQL file
sql_file = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'db_sql', '003_llm_analysis_tables.sql')
with open(sql_file, 'r') as f:
    sql = f.read()

# Connect to Supabase using environment variables
url = os.getenv('SUPABASE_URL')
# Try both SUPABASE_KEY and SUPABASE_ANON_KEY (different env files use different names)
key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY) must be set in backend/.env")

print(f"Connecting to Supabase at {url}...")
supabase = create_client(url, key)

# Execute SQL
try:
    # Split SQL into individual statements (rough split by semicolons)
    statements = []
    current_statement = []
    in_function = False
    
    for line in sql.split('\n'):
        stripped = line.strip()
        
        # Track if we're inside a function definition
        if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
            in_function = True
        
        current_statement.append(line)
        
        # End of statement detection
        if stripped.endswith(';') and not in_function:
            statements.append('\n'.join(current_statement))
            current_statement = []
        elif in_function and stripped.startswith('$$ LANGUAGE'):
            in_function = False
    
    # Add any remaining statement
    if current_statement:
        statements.append('\n'.join(current_statement))
    
    print(f"\nExecuting {len(statements)} SQL statements...\n")
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements):
        statement = statement.strip()
        
        # Skip empty statements and comments
        if not statement or statement.startswith('--') or len(statement) < 10:
            continue
        
        # Show what we're executing
        first_line = statement.split('\n')[0][:80]
        print(f"[{i+1}] {first_line}...")
        
        try:
            # Use the Supabase REST API to execute raw SQL
            # Note: This requires proper permissions
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            print(f"    ✓ Success")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            # Some errors are expected (like "already exists")
            if 'already exists' in error_msg.lower() or 'if not exists' in statement.lower():
                print(f"    ⚠ Already exists (skipped)")
                success_count += 1
            else:
                print(f"    ✗ Error: {error_msg[:100]}")
                error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Migration Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*60}")
    
    if error_count == 0:
        print("\n✅ LLM analysis tables migration completed successfully!")
    else:
        print(f"\n⚠️  Migration completed with {error_count} errors. Check output above.")

except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
