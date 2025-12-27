-- ============================================
-- FIX MISSING COLUMNS IN CRAWLS TABLE
-- ============================================
-- Add missing columns that weren't in the original table

-- Add concurrency column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'crawls'
      AND column_name = 'concurrency'
  ) THEN
    ALTER TABLE crawls ADD COLUMN concurrency INT NOT NULL DEFAULT 5;
  END IF;
END $$;

-- Add name column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'crawls'
      AND column_name = 'name'
  ) THEN
    ALTER TABLE crawls ADD COLUMN name TEXT;
  END IF;
END $$;

-- Verify the columns now exist
SELECT
  'crawls table columns:' as info,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'crawls'
ORDER BY ordinal_position;