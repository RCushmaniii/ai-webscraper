#!/usr/bin/env python3
"""Update all endpoints in crawls.py to use authenticated client"""
import re
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

file_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'api', 'routes', 'crawls.py')

print("=" * 70)
print("UPDATING CRAWLS.PY TO USE AUTHENTICATED CLIENT")
print("=" * 70)

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Track changes
changes = 0

# Pattern 1: supabase_client.table( -> auth_client.table(
# But we need to add auth_client = get_auth_client() first in each function

# List of functions that need updating (excluding list_crawls which is already done)
functions_to_update = [
    'create_crawl',
    'get_crawl',
    'mark_crawl_failed',
    'delete_crawl',
    'list_crawl_pages',
    'get_page_detail',
    'list_crawl_links',
    'list_crawl_images',
    'list_crawl_issues',
    'get_crawl_summary',
    'get_page_html',
    'get_page_screenshot',
    'get_comprehensive_audit',
    '_get_basic_audit_data'
]

# Replace supabase_client.table with auth_client.table in endpoints
# We'll do a simple replacement for all instances
new_content = content.replace('supabase_client.table(', 'auth_client.table(')
if new_content != content:
    changes += new_content.count('auth_client.table(') - content.count('auth_client.table(')
    print(f"✓ Replaced {changes} instances of supabase_client.table() with auth_client.table()")
    content = new_content

# Now we need to add auth_client = get_auth_client() at the start of each function
# Find each function and add the line after the try: statement

for func_name in functions_to_update:
    # Pattern to match the function and add auth_client assignment after try:
    # Look for: async def func_name(...): ... try:
    pattern = rf'(async def {func_name}\([^)]+\)[^:]*:\s+"""[^"]*"""\s+(?:if[^:]+:\s+[^\n]+\s+)?try:)'

    replacement = r'\1\n        # Use authenticated client for RLS\n        auth_client = get_auth_client()\n'

    new_content = re.sub(pattern, replacement, content, count=1)
    if new_content != content:
        print(f"✓ Added auth_client initialization to {func_name}()")
        content = new_content
        changes += 1

# Write the updated file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✓ Successfully updated {changes} locations in crawls.py")
print("=" * 70)