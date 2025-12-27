-- Check what constraints exist on crawls table
SELECT
  conname AS constraint_name,
  pg_get_constraintdef(c.oid) AS constraint_definition
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE conrelid = 'public.crawls'::regclass
  AND contype = 'c';  -- 'c' = check constraint