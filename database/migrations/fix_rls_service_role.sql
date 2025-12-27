-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can insert their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

-- Create proper policies with service role bypass
CREATE POLICY "Users can view their own data" ON users
  FOR SELECT USING (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can insert their own data" ON users
  FOR INSERT WITH CHECK (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can update their own data" ON users
  FOR UPDATE USING (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

-- Keep RLS enabled
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
