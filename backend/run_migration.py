"""
Run database migration to add depth column to links table
"""
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Create service role client (bypasses RLS)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# SQL to add depth column
migration_sql = """
-- Add missing depth column to links table
ALTER TABLE links ADD COLUMN IF NOT EXISTS depth INTEGER DEFAULT 0;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_links_depth ON links(crawl_id, depth);

-- Update existing rows to have depth 0
UPDATE links SET depth = 0 WHERE depth IS NULL;
"""

try:
    print("Running migration to add depth column to links table...")
    
    # Execute the migration using RPC
    result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
    
    print("✅ Migration completed successfully!")
    print(f"Result: {result}")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    print("\nTrying alternative approach...")
    
    # Alternative: Run each statement separately
    statements = [
        "ALTER TABLE links ADD COLUMN IF NOT EXISTS depth INTEGER DEFAULT 0",
        "CREATE INDEX IF NOT EXISTS idx_links_depth ON links(crawl_id, depth)",
        "UPDATE links SET depth = 0 WHERE depth IS NULL"
    ]
    
    for stmt in statements:
        try:
            print(f"Executing: {stmt[:50]}...")
            supabase.postgrest.rpc('exec_sql', {'sql': stmt}).execute()
            print("✅ Success")
        except Exception as stmt_error:
            print(f"⚠️  Statement failed: {stmt_error}")
            print("You need to run this SQL manually in Supabase SQL Editor:")
            print("\n" + migration_sql)
            break
