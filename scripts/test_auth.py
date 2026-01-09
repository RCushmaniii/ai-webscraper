#!/usr/bin/env python3
"""Test authentication flow"""
import requests
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

BACKEND_URL = "http://localhost:8000/api/v1"
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print("="*70)
print("TESTING AUTHENTICATION")
print("="*70)
print(f"\nBackend URL: {BACKEND_URL}")
print(f"Supabase URL: {SUPABASE_URL}")
print(f"Supabase Key: {SUPABASE_KEY[:20]}...")

# Test 1: Backend health
print("\n[TEST 1] Backend Health...")
try:
    r = requests.get(f"{BACKEND_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: LLM Status (should work without auth)
print("\n[TEST 2] LLM Status Endpoint...")
try:
    r = requests.get(f"{BACKEND_URL}/analysis/status")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Create a test user token with Supabase
print("\n[TEST 3] Testing with Supabase Auth...")
from supabase import create_client

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Try to get current session
    session = supabase.auth.get_session()

    if session and session.access_token:
        print(f"Active session found!")
        print(f"Token: {session.access_token[:30]}...")

        # Test /users/me with token
        headers = {
            'Authorization': f'Bearer {session.access_token}',
            'Content-Type': 'application/json'
        }

        r = requests.get(f"{BACKEND_URL}/users/me", headers=headers)
        print(f"\n/users/me Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
    else:
        print("No active session - would need to login first")
        print("This is expected if you haven't logged in recently")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("Auth test complete!")
print("="*70)