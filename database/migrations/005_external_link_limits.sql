-- ============================================================================
-- External Link Limits & Safety Migration
-- ============================================================================
--
-- Adds safety controls for following external links:
-- 1. max_external_links: Limit how many external domains to follow (default 5)
-- 2. Removes duplicate follow_external field (database has follow_external_links)
--
-- ============================================================================

-- Add max_external_links column
ALTER TABLE crawls
ADD COLUMN IF NOT EXISTS max_external_links INTEGER DEFAULT 5;

-- Add comment
COMMENT ON COLUMN crawls.max_external_links IS
  'Maximum number of external domains to follow (prevents crawling entire internet)';

-- Update existing crawls to have the default
UPDATE crawls
SET max_external_links = 5
WHERE max_external_links IS NULL;

-- Add check constraint to prevent unreasonable values
ALTER TABLE crawls
ADD CONSTRAINT max_external_links_reasonable
CHECK (max_external_links >= 0 AND max_external_links <= 50);

-- Verification
SELECT
  column_name,
  data_type,
  column_default,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'crawls'
AND column_name IN ('follow_external_links', 'external_depth', 'max_external_links')
ORDER BY column_name;