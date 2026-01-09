-- Comprehensive migration to add all missing columns to match crawler expectations

-- Fix LINKS table
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_internal BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE links ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS latency_ms INTEGER;
ALTER TABLE links ADD COLUMN IF NOT EXISTS anchor_text TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_nofollow BOOLEAN DEFAULT false;

-- Fix IMAGES table - rename alt_text to alt
ALTER TABLE images RENAME COLUMN IF EXISTS alt_text TO alt;

-- If the rename didn't work (column doesn't exist), add it
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'images' AND column_name = 'alt') THEN
        ALTER TABLE images ADD COLUMN alt TEXT;
    END IF;
END $$;

-- Ensure all service role policies exist
DROP POLICY IF EXISTS "Service role can insert pages" ON pages;
CREATE POLICY "Service role can insert pages" ON pages
  FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can update pages" ON pages;
CREATE POLICY "Service role can update pages" ON pages
  FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Service role can select pages" ON pages;
CREATE POLICY "Service role can select pages" ON pages
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Service role can insert links" ON links;
CREATE POLICY "Service role can insert links" ON links
  FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can update links" ON links;
CREATE POLICY "Service role can update links" ON links
  FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Service role can select links" ON links;
CREATE POLICY "Service role can select links" ON links
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "Service role can insert images" ON images;
CREATE POLICY "Service role can insert images" ON images
  FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can update images" ON images;
CREATE POLICY "Service role can update images" ON images
  FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Service role can select images" ON images;
CREATE POLICY "Service role can select images" ON images
  FOR SELECT USING (true);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_links_is_internal ON links(crawl_id, is_internal);
CREATE INDEX IF NOT EXISTS idx_links_error ON links(crawl_id) WHERE error IS NOT NULL;
