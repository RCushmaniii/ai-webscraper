"""Check database schema to verify all columns exist"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("=== CHECKING DATABASE SCHEMA ===\n")

# Test links table
print("LINKS TABLE:")
try:
    test_link = {
        'crawl_id': '00000000-0000-0000-0000-000000000000',
        'target_url': 'https://test.com',
        'is_internal': True,
        'depth': 1,
        'source_page_id': '00000000-0000-0000-0000-000000000000'
    }
    result = client.table('links').insert(test_link).execute()
    print("✅ target_url: EXISTS")
    print("✅ is_internal: EXISTS")
    print("✅ depth: EXISTS")
    print("✅ source_page_id: EXISTS")
    # Clean up test data
    client.table('links').delete().eq('target_url', 'https://test.com').execute()
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\nIMAGES TABLE:")
try:
    test_image = {
        'crawl_id': '00000000-0000-0000-0000-000000000000',
        'url': 'https://test.com/image.jpg',
        'alt': 'Test image'
    }
    result = client.table('images').insert(test_image).execute()
    print("✅ url: EXISTS")
    print("✅ alt: EXISTS")
    # Clean up test data
    client.table('images').delete().eq('url', 'https://test.com/image.jpg').execute()
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n=== SCHEMA CHECK COMPLETE ===")
