-- Add missing columns to users table if they don't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;

-- Fix RLS policies for users table to allow service role access
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can insert their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

-- Create policies with service role bypass
CREATE POLICY "Users can view their own data" ON users
  FOR SELECT USING (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can insert their own data" ON users
  FOR INSERT WITH CHECK (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can update their own data" ON users
  FOR UPDATE USING (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

-- Keep RLS enabled
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
