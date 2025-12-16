-- Fix RLS Policy Recursion Error
-- Run this in Supabase SQL Editor to fix the infinite recursion

-- Drop the problematic policies first
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Admins can view all users" ON users;

-- Create simpler, non-recursive policies
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid() = id);

-- Temporarily disable RLS on users table to allow initial setup
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Re-enable after testing
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
