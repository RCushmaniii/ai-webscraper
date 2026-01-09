#!/usr/bin/env python3
"""Test backend crawls endpoint directly"""
import requests
import json

print("="*70)
print("TESTING BACKEND /crawls ENDPOINT")
print("="*70)

# Get a real session from Supabase
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"\nSupabase URL: {url}")

supabase = create_client(url, key)

# Try to get current session
session = supabase.auth.get_session()

if not session:
    print("\n[ERROR] No active session!")
    print("You need to login in the browser first, then run this script again.")
    exit(1)

token = session.access_token
print(f"\n[OK] Got auth token: {token[:30]}...")

# Test the backend
backend_url = "http://localhost:8000/api/v1"

print(f"\n[TEST 1] Testing /users/me...")
r = requests.get(
    f"{backend_url}/users/me",
    headers={'Authorization': f'Bearer {token}'}
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

print(f"\n[TEST 2] Testing /crawls/...")
r = requests.get(
    f"{backend_url}/crawls/",
    headers={'Authorization': f'Bearer {token}'}
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Crawls returned: {len(data)}")
    if len(data) > 0:
        print(f"First crawl: {json.dumps(data[0], indent=2)[:200]}")
else:
    print(f"Response: {r.text[:500]}")

print("\n" + "="*70)