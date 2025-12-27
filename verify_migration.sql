-- ============================================
-- VERIFICATION SCRIPT
-- Run this AFTER the migration to verify everything is correct
-- ============================================

-- 1. Check all expected tables exist
SELECT
  'Expected tables' as check_type,
  CASE
    WHEN COUNT(*) = 11 THEN '✅ PASS - All 11 tables exist'
    ELSE '❌ FAIL - Missing tables. Found: ' || COUNT(*) || ' Expected: 11'
  END as result
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'users', 'crawls', 'pages', 'seo_metadata', 'links',
    'issues', 'summaries', 'batches', 'batch_sites',
    'audit_log', 'google_places'
  );

-- 2. Check all tables have RLS enabled
SELECT
  'RLS enabled' as check_type,
  CASE
    WHEN COUNT(*) = 11 THEN '✅ PASS - All 11 tables have RLS enabled'
    ELSE '❌ FAIL - Some tables missing RLS. Count: ' || COUNT(*)
  END as result
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = true
  AND tablename IN (
    'users', 'crawls', 'pages', 'seo_metadata', 'links',
    'issues', 'summaries', 'batches', 'batch_sites',
    'audit_log', 'google_places'
  );

-- 3. Check critical policies exist (minimum 4 per table for CRUD)
SELECT
  'RLS policies' as check_type,
  CASE
    WHEN COUNT(*) >= 40 THEN '✅ PASS - ' || COUNT(*) || ' policies found (≥40 expected)'
    ELSE '❌ FAIL - Only ' || COUNT(*) || ' policies found (≥40 expected)'
  END as result
FROM pg_policies
WHERE schemaname = 'public';

-- 4. Check foreign key constraints
SELECT
  'Foreign keys' as check_type,
  CASE
    WHEN COUNT(*) >= 14 THEN '✅ PASS - ' || COUNT(*) || ' foreign keys found'
    ELSE '⚠️ WARNING - Only ' || COUNT(*) || ' foreign keys found'
  END as result
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
  AND table_schema = 'public';

-- 5. Check performance indexes
SELECT
  'Performance indexes' as check_type,
  CASE
    WHEN COUNT(*) >= 15 THEN '✅ PASS - ' || COUNT(*) || ' indexes found'
    ELSE '⚠️ WARNING - Only ' || COUNT(*) || ' indexes (15+ recommended)'
  END as result
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname NOT LIKE '%_pkey';

-- 6. Detailed table and policy status
SELECT
  tablename as table_name,
  (SELECT COUNT(*) FROM pg_policies p WHERE p.tablename = t.tablename AND p.schemaname = 'public') as policy_count,
  CASE WHEN rowsecurity THEN 'YES' ELSE 'NO' END as rls_enabled
FROM pg_tables t
WHERE schemaname = 'public'
ORDER BY tablename;

-- 7. List all policies for review
SELECT
  tablename,
  policyname,
  cmd as operation,
  CASE
    WHEN permissive = 'PERMISSIVE' THEN 'PERMISSIVE'
    ELSE 'RESTRICTIVE'
  END as type
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd, policyname;