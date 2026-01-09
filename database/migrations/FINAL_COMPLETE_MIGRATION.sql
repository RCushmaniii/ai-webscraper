-- FINAL COMPLETE MIGRATION - Run this ONE SQL script in Supabase SQL Editor
-- This adds ALL missing columns to match what the crawler expects

-- ============================================
-- LINKS TABLE - Add all missing columns
-- ============================================
ALTER TABLE links ADD COLUMN IF NOT EXISTS target_url TEXT NOT NULL DEFAULT '';
ALTER TABLE links ADD COLUMN IF NOT EXISTS source_page_id UUID REFERENCES pages(id) ON DELETE CASCADE;
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_internal BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE links ADD COLUMN IF NOT EXISTS depth INTEGER DEFAULT 0;
ALTER TABLE links ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS latency_ms INTEGER;
ALTER TABLE links ADD COLUMN IF NOT EXISTS anchor_text TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_nofollow BOOLEAN DEFAULT false;
ALTER TABLE links ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE links ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- ============================================
-- IMAGES TABLE - Ensure it exists with correct columns
-- ============================================
CREATE TABLE IF NOT EXISTS images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  alt TEXT,
  width INTEGER,
  height INTEGER,
  file_size INTEGER,
  format TEXT,
  is_broken BOOLEAN DEFAULT FALSE,
  status_code INTEGER,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- RLS POLICIES - Service role bypass for all tables
-- ============================================
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE links ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;

-- Drop existing service role policies
DROP POLICY IF EXISTS "Service role can insert pages" ON pages;
DROP POLICY IF EXISTS "Service role can update pages" ON pages;
DROP POLICY IF EXISTS "Service role can select pages" ON pages;
DROP POLICY IF EXISTS "Service role can insert links" ON links;
DROP POLICY IF EXISTS "Service role can update links" ON links;
DROP POLICY IF EXISTS "Service role can select links" ON links;
DROP POLICY IF EXISTS "Service role can insert images" ON images;
DROP POLICY IF EXISTS "Service role can update images" ON images;
DROP POLICY IF EXISTS "Service role can select images" ON images;
DROP POLICY IF EXISTS "Users can view their own images" ON images;
DROP POLICY IF EXISTS "Users can insert images" ON images;

-- Create service role policies (bypass RLS for Celery worker)
CREATE POLICY "Service role can insert pages" ON pages FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update pages" ON pages FOR UPDATE USING (true);
CREATE POLICY "Service role can select pages" ON pages FOR SELECT USING (true);

CREATE POLICY "Service role can insert links" ON links FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update links" ON links FOR UPDATE USING (true);
CREATE POLICY "Service role can select links" ON links FOR SELECT USING (true);

CREATE POLICY "Service role can insert images" ON images FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update images" ON images FOR UPDATE USING (true);
CREATE POLICY "Service role can select images" ON images FOR SELECT USING (true);

-- User policies for images
CREATE POLICY "Users can view their own images" ON images
  FOR SELECT
  USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = images.crawl_id AND crawls.user_id = auth.uid()));

CREATE POLICY "Users can insert images" ON images
  FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = images.crawl_id AND crawls.user_id = auth.uid()));

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_links_crawl_id ON links(crawl_id);
CREATE INDEX IF NOT EXISTS idx_links_target_url ON links(crawl_id, target_url);
CREATE INDEX IF NOT EXISTS idx_links_depth ON links(crawl_id, depth);
CREATE INDEX IF NOT EXISTS idx_links_is_internal ON links(crawl_id, is_internal);
CREATE INDEX IF NOT EXISTS idx_links_error ON links(crawl_id) WHERE error IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_images_crawl_id ON images(crawl_id);
CREATE INDEX IF NOT EXISTS idx_images_page_id ON images(page_id);
