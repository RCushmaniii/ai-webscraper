-- Add missing depth column to links table
-- This column is required for the crawler to track link depth

ALTER TABLE links ADD COLUMN IF NOT EXISTS depth INTEGER DEFAULT 0;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_links_depth ON links(crawl_id, depth);

-- Update existing rows to have depth 0
UPDATE links SET depth = 0 WHERE depth IS NULL;
