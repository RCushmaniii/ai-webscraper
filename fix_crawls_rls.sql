-- Fix RLS policies for crawls table to allow service role access
-- This allows the backend (using service role key) to create crawls

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can insert their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can update their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can delete their own crawls" ON crawls;

-- Create policies with service role bypass
CREATE POLICY "Users can view their own crawls" ON crawls
  FOR SELECT USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can insert their own crawls" ON crawls
  FOR INSERT WITH CHECK (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can update their own crawls" ON crawls
  FOR UPDATE USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can delete their own crawls" ON crawls
  FOR DELETE USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

-- Keep RLS enabled
ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;
