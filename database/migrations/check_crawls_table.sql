-- Check actual columns in crawls table
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'crawls'
ORDER BY ordinal_position;