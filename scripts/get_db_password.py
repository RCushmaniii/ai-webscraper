#!/usr/bin/env python3
"""Attempt to retrieve database password from Supabase"""
import os
import sys
from dotenv import load_dotenv
import getpass

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

print("="*70)
print("DATABASE PASSWORD SETUP")
print("="*70)
print("\nI need your Supabase database password to run the migration.")
print("This will be saved to .env and you'll never need to enter it again.")
print("\nWhere to find it:")
print("  Dashboard > Project Settings > Database > Database Password")
print("\nIt looks like: ************ (hidden)")
print("\nEnter it below (input will be hidden):")

db_password = getpass.getpass("Database Password: ")

if not db_password:
    print("\n[ERROR] No password provided")
    sys.exit(1)

# Save to .env
env_file = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
with open(env_file, 'a', encoding='utf-8') as f:
    f.write(f"\n# Supabase Database Password\nSUPABASE_DB_PASSWORD={db_password}\n")

print("\n[OK] Password saved to .env")
print("[OK] Running migration now...")

# Run the migration script
import subprocess
migration_script = os.path.join(os.path.dirname(__file__), 'run_migration_programmatic.py')
result = subprocess.run([sys.executable, migration_script], capture_output=False)

sys.exit(result.returncode)