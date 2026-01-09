#!/usr/bin/env python3
"""Execute SQL migration using psycopg2 direct connection"""
import os
import sys
import re
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read SQL file from command line argument or use default
if len(sys.argv) > 1:
    sql_file = sys.argv[1]
    if not os.path.isabs(sql_file):
        sql_file = os.path.join(os.getcwd(), sql_file)
else:
    sql_file = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'db_sql', '003_llm_analysis_tables.sql')

if not os.path.exists(sql_file):
    print(f"ERROR: SQL file not found: {sql_file}")
    sys.exit(1)

with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Get credentials
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

# Extract project ref
match = re.search(r'https://([^.]+)\.supabase\.co', url)
if not match:
    print("ERROR: Could not extract project ref from SUPABASE_URL")
    sys.exit(1)

project_ref = match.group(1)

print("=" * 70)
print("LLM MIGRATION EXECUTION")
print("=" * 70)
print(f"\nProject: {project_ref}")
print(f"SQL File: {sql_file}")
print(f"SQL Size: {len(sql_content)} characters")

# Try to install psycopg2 if not available
try:
    import psycopg2
    print("\n[OK] psycopg2 is available")
except ImportError:
    print("\n[WARN] psycopg2 not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    print("[OK] psycopg2 installed")

# Check for database password in environment
db_password = os.getenv('SUPABASE_DB_PASSWORD')

if not db_password:
    print("\n" + "=" * 70)
    print("DATABASE PASSWORD REQUIRED")
    print("=" * 70)
    print("\nThe database password is not set in your .env file.")
    print("You can find it in your Supabase project settings:")
    print("  1. Go to https://supabase.com/dashboard")
    print(f"  2. Open project: {project_ref}")
    print("  3. Settings > Database > Connection string")
    print("  4. Copy the password")
    print("\nThen add to backend/.env:")
    print("SUPABASE_DB_PASSWORD=your-password-here")
    print("\nOr enter it now (it will be saved to .env):")

    # Read password from input
    db_password = input("Database Password: ").strip()

    if db_password:
        # Save to .env
        env_file = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
        with open(env_file, 'a') as f:
            f.write(f"\n# Supabase Database Password\nSUPABASE_DB_PASSWORD={db_password}\n")
        print("[OK] Password saved to .env")
    else:
        print("ERROR: Password is required")
        sys.exit(1)

# Construct connection string
conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"

print("\n" + "=" * 70)
print("EXECUTING MIGRATION")
print("=" * 70)

try:
    # Connect to database
    print("\n[1/3] Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = False
    cursor = conn.cursor()
    print("[OK] Connected successfully")

    # Execute SQL
    print("\n[2/3] Executing SQL migration...")
    try:
        cursor.execute(sql_content)
        conn.commit()
        print("[OK] Migration executed successfully")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")

        # Check if tables already exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('page_analysis', 'crawl_analysis', 'page_embeddings', 'llm_usage', 'image_analysis')
        """)
        existing = cursor.fetchall()

        if existing:
            print(f"\n[WARN] Note: Some tables already exist: {[t[0] for t in existing]}")
            print("This is OK if you're re-running the migration.")
        else:
            raise

    # Verify tables were created
    print("\n[3/3] Verifying tables...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('page_analysis', 'crawl_analysis', 'page_embeddings', 'llm_usage', 'image_analysis')
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    print(f"[OK] Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Close connection
    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("SUCCESS! MIGRATION COMPLETED")
    print("=" * 70)
    print(f"\nMigration file: {os.path.basename(sql_file)}")
    print("All schema changes have been applied.")

except psycopg2.OperationalError as e:
    print(f"\n[ERROR] Connection failed: {e}")
    print("\nPlease verify:")
    print("  1. Database password is correct")
    print("  2. Your IP is allowed in Supabase (check Network Restrictions)")
    print("  3. Database is online")
    sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)