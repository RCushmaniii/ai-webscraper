#!/usr/bin/env python3
"""Check table schemas"""
import os
import sys
import re
from dotenv import load_dotenv
import psycopg2

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

url = os.getenv('SUPABASE_URL')
db_pass = os.getenv('SUPABASE_DB_PASSWORD')
match = re.search(r'https://([^.]+)\.supabase\.co', url)
project_ref = match.group(1)
conn_string = f'postgresql://postgres:{db_pass}@db.{project_ref}.supabase.co:5432/postgres'

conn = psycopg2.connect(conn_string)
cursor = conn.cursor()

# Check images table columns
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'images'
    ORDER BY ordinal_position
""")
print('IMAGES TABLE COLUMNS:')
for col, dtype in cursor.fetchall():
    print(f'  {col}: {dtype}')

# Check links table columns
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'links'
    ORDER BY ordinal_position
""")
print('\nLINKS TABLE COLUMNS:')
for col, dtype in cursor.fetchall():
    print(f'  {col}: {dtype}')

# Check pages table columns
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'pages'
    ORDER BY ordinal_position
""")
print('\nPAGES TABLE COLUMNS:')
for col, dtype in cursor.fetchall():
    print(f'  {col}: {dtype}')

cursor.close()
conn.close()
