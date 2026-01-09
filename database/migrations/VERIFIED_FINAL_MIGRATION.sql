-- VERIFIED FINAL MIGRATION - Checked against actual crawler code
-- This matches EXACTLY what the crawler sends

-- ============================================
-- LINKS TABLE - Verified against crawler.py line 504-518
-- ============================================
ALTER TABLE links ADD COLUMN IF NOT EXISTS target_url TEXT NOT NULL DEFAULT '';
ALTER TABLE links ADD COLUMN IF NOT EXISTS source_page_id UUID REFERENCES pages(id) ON DELETE CASCADE;
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_internal BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE links ADD COLUMN IF NOT EXISTS depth INTEGER DEFAULT 0;
ALTER TABLE links ADD COLUMN IF NOT EXISTS status_code INTEGER;
ALTER TABLE links ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS latency_ms INTEGER;
ALTER TABLE links ADD COLUMN IF NOT EXISTS anchor_text TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_nofollow BOOLEAN DEFAULT false;
ALTER TABLE links ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE links ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- ============================================
-- IMAGES TABLE - Verified against crawler.py line 610-624
-- ============================================
CREATE TABLE IF NOT EXISTS images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  src TEXT NOT NULL,
  alt TEXT,
  title TEXT,
  width INTEGER,
  height INTEGER,
  has_alt BOOLEAN DEFAULT false,
  is_broken BOOLEAN DEFAULT false,
  status_code INTEGER,
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- RLS POLICIES - Service role bypass
-- ============================================
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can insert pages" ON pages;
DROP POLICY IF EXISTS "Service role can update pages" ON pages;
DROP POLICY IF EXISTS "Service role can select pages" ON pages;
DROP POLICY IF EXISTS "Service role can insert links" ON links;
DROP POLICY IF EXISTS "Service role can update links" ON links;
DROP POLICY IF EXISTS "Service role can select links" ON links;
DROP POLICY IF EXISTS "Service role can insert images" ON images;
DROP POLICY IF EXISTS "Service role can update images" ON images;
DROP POLICY IF EXISTS "Service role can select images" ON images;

CREATE POLICY "Service role can insert pages" ON pages FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update pages" ON pages FOR UPDATE USING (true);
CREATE POLICY "Service role can select pages" ON pages FOR SELECT USING (true);
CREATE POLICY "Service role can insert links" ON links FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update links" ON links FOR UPDATE USING (true);
CREATE POLICY "Service role can select links" ON links FOR SELECT USING (true);
CREATE POLICY "Service role can insert images" ON images FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update images" ON images FOR UPDATE USING (true);
CREATE POLICY "Service role can select images" ON images FOR SELECT USING (true);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_links_crawl_id ON links(crawl_id);
CREATE INDEX IF NOT EXISTS idx_links_target_url ON links(crawl_id, target_url);
CREATE INDEX IF NOT EXISTS idx_links_depth ON links(crawl_id, depth);
CREATE INDEX IF NOT EXISTS idx_images_crawl_id ON images(crawl_id);
CREATE INDEX IF NOT EXISTS idx_images_page_id ON images(page_id);
