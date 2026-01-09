-- Create images table for storing image metadata from crawls
CREATE TABLE IF NOT EXISTS images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  alt_text TEXT,
  width INTEGER,
  height INTEGER,
  file_size INTEGER,
  format TEXT,
  is_broken BOOLEAN DEFAULT FALSE,
  status_code INTEGER,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own images" ON images;
DROP POLICY IF EXISTS "Service role can insert images" ON images;
DROP POLICY IF EXISTS "Users can insert images" ON images;

-- RLS Policies for images
CREATE POLICY "Users can view their own images" ON images
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = images.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert images" ON images
  FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Users can insert images" ON images
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = images.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_images_crawl_id ON images(crawl_id);
CREATE INDEX IF NOT EXISTS idx_images_page_id ON images(page_id);
CREATE INDEX IF NOT EXISTS idx_images_broken ON images(crawl_id) WHERE is_broken = TRUE;

-- Fix pages table RLS - add service role bypass
DROP POLICY IF EXISTS "Service role can insert pages" ON pages;
CREATE POLICY "Service role can insert pages" ON pages
  FOR INSERT
  WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can update pages" ON pages;
CREATE POLICY "Service role can update pages" ON pages
  FOR UPDATE
  USING (true);

-- Fix links table RLS - add service role bypass  
DROP POLICY IF EXISTS "Service role can insert links" ON links;
CREATE POLICY "Service role can insert links" ON links
  FOR INSERT
  WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can update links" ON links;
CREATE POLICY "Service role can update links" ON links
  FOR UPDATE
  USING (true);
