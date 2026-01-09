#!/usr/bin/env python3
"""Automatically open Supabase SQL Editor with migration SQL copied to clipboard"""
import os
import sys
import webbrowser
import re
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Read SQL
sql_file = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'db_sql', '003_llm_analysis_tables.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Get project ref
url = os.getenv('SUPABASE_URL')
match = re.search(r'https://([^.]+)\.supabase\.co', url)
project_ref = match.group(1) if match else None

if not project_ref:
    print("ERROR: Could not extract project ref from SUPABASE_URL")
    sys.exit(1)

print("="*70)
print("SUPABASE MIGRATION AUTOMATION")
print("="*70)
print(f"\nProject: {project_ref}")
print(f"SQL File: {sql_file}")
print(f"SQL Size: {len(sql_content)} characters\n")

# Try to copy to clipboard
try:
    import pyperclip
    pyperclip.copy(sql_content)
    print("[OK] SQL copied to clipboard!")
    clipboard_success = True
except ImportError:
    print("[INFO] Installing pyperclip for clipboard support...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import pyperclip
        pyperclip.copy(sql_content)
        print("[OK] SQL copied to clipboard!")
        clipboard_success = True
    except:
        print("[WARN] Could not copy to clipboard (pyperclip failed)")
        clipboard_success = False

# Open Supabase SQL Editor
sql_editor_url = f"https://supabase.com/dashboard/project/{project_ref}/sql/new"

print(f"\n[ACTION] Opening Supabase SQL Editor...")
print(f"URL: {sql_editor_url}\n")

# Open browser
webbrowser.open(sql_editor_url)

print("="*70)
print("NEXT STEPS:")
print("="*70)

if clipboard_success:
    print("\n1. The SQL has been copied to your clipboard")
    print("2. The Supabase SQL Editor should open in your browser")
    print("3. Paste (Ctrl+V) the SQL into the editor")
    print("4. Click the 'Run' button (or press F5)")
    print("\nThat's it! The migration will execute.")
else:
    print("\n1. The Supabase SQL Editor should open in your browser")
    print("2. Copy the SQL from this file:")
    print(f"   {sql_file}")
    print("3. Paste it into the SQL editor")
    print("4. Click 'Run'")

print("\n" + "="*70)
print("Waiting for you to complete the migration in Supabase...")
print("="*70)

input("\nPress ENTER after you've run the migration in Supabase... ")

print("\n[OK] Migration marked as complete!")
print("\nThe LLM analysis features should now be available.")
print("Continuing with setup...")