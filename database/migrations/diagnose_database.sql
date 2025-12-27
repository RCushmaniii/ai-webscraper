-- ============================================
-- DATABASE DIAGNOSTIC SCRIPT
-- Run this to see the current state of your database
-- ============================================

-- 1. List all tables in public schema
SELECT
  'TABLES' as category,
  table_name,
  NULL as details
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. Check which tables have RLS enabled
SELECT
  'RLS STATUS' as category,
  tablename as table_name,
  CASE WHEN rowsecurity THEN 'ENABLED' ELSE 'DISABLED' END as details
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 3. List all RLS policies
SELECT
  'POLICIES' as category,
  tablename as table_name,
  policyname || ' (' || cmd || ')' as details
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- 4. List all foreign key constraints
SELECT
  'FOREIGN KEYS' as category,
  tc.table_name,
  kcu.column_name || ' -> ' || ccu.table_name || '(' || ccu.column_name || ')' as details
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- 5. List all indexes
SELECT
  'INDEXES' as category,
  tablename as table_name,
  indexname as details
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname NOT LIKE '%_pkey'
ORDER BY tablename, indexname;

-- 6. Check users table structure
SELECT
  'USERS COLUMNS' as category,
  column_name as table_name,
  data_type || COALESCE(' (' || character_maximum_length || ')', '') as details
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'users'
ORDER BY ordinal_position;

-- 7. Check crawls table structure
SELECT
  'CRAWLS COLUMNS' as category,
  column_name as table_name,
  data_type || COALESCE(' (' || character_maximum_length || ')', '') as details
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'crawls'
ORDER BY ordinal_position;