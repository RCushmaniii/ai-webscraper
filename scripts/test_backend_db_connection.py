#!/usr/bin/env python3
"""Test if backend can connect to Supabase"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

print("="*70)
print("TESTING BACKEND SUPABASE CONNECTION")
print("="*70)

# Test Supabase client
from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"\nSupabase URL: {url}")
print(f"Supabase Key: {key[:20]}...")

try:
    client = create_client(url, key)
    print("\n[OK] Supabase client created")

    # Try to query users table
    print("\n[TEST] Querying users table...")
    result = client.table('users').select('*').limit(1).execute()

    if result.data:
        print(f"[OK] Got {len(result.data)} user(s)")
        print(f"User: {result.data[0].get('email')}")
    else:
        print("[WARN] No users found")

    # Try to query crawls table
    print("\n[TEST] Querying crawls table...")
    result = client.table('crawls').select('*').limit(5).execute()

    if result.data:
        print(f"[OK] Got {len(result.data)} crawl(s)")
        for crawl in result.data:
            print(f"  - {crawl.get('url')} (user_id: {crawl.get('user_id')})")
    else:
        print("[WARN] No crawls found")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)