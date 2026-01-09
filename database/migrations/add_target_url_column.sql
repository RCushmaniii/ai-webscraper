-- Add target_url column to links table (don't rename, just add)
ALTER TABLE links ADD COLUMN IF NOT EXISTS target_url TEXT;

-- Copy data from url column if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'links' AND column_name = 'url') THEN
        UPDATE links SET target_url = url WHERE target_url IS NULL;
    END IF;
END $$;

-- Make target_url NOT NULL after copying data
ALTER TABLE links ALTER COLUMN target_url SET NOT NULL;

-- Ensure source_page_id exists
ALTER TABLE links ADD COLUMN IF NOT EXISTS source_page_id UUID REFERENCES pages(id) ON DELETE CASCADE;

-- Add index
CREATE INDEX IF NOT EXISTS idx_links_target_url ON links(crawl_id, target_url);
