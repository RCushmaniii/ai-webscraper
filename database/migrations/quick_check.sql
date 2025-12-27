-- Quick check: Do the tables exist?
SELECT
  table_name,
  CASE
    WHEN table_name IN ('users', 'crawls', 'pages', 'seo_metadata', 'links', 'issues', 'summaries', 'batches', 'batch_sites', 'audit_log', 'google_places')
    THEN '✅ Expected'
    ELSE '❓ Unexpected'
  END as status
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check if crawls table has correct columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'crawls'
ORDER BY ordinal_position;
