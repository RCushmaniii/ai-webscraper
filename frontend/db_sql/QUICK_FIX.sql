-- Quick Fix for Authentication Issues
-- Run this in Supabase SQL Editor

-- 1. Temporarily disable RLS on users table to fix recursion
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- 2. Verify your admin user exists
SELECT id, email, is_admin FROM users WHERE email = 'rcushmaniii+admin@gmail.com';

-- 3. If the user doesn't exist, insert it (replace UUID with your actual auth user ID)
-- INSERT INTO users (id, email, is_admin) 
-- VALUES ('13057f6d-2939-4f90-8893-515c643cc61c', 'rcushmaniii+admin@gmail.com', true)
-- ON CONFLICT (id) DO UPDATE SET is_admin = true;
