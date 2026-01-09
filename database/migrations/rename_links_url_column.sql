-- Rename url to target_url in links table to match crawler expectations
ALTER TABLE links RENAME COLUMN url TO target_url;

-- Ensure source_page_id exists (should already exist)
ALTER TABLE links ADD COLUMN IF NOT EXISTS source_page_id UUID REFERENCES pages(id) ON DELETE CASCADE;

-- Add index on target_url for performance
CREATE INDEX IF NOT EXISTS idx_links_target_url ON links(crawl_id, target_url);
