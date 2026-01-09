-- DROP AND RECREATE tables with EXACT schema from crawler.py
-- This matches the exact columns the crawler sends

-- Drop existing tables (will cascade delete data)
DROP TABLE IF EXISTS images CASCADE;
DROP TABLE IF EXISTS links CASCADE;

-- ============================================
-- LINKS TABLE - Exact schema from crawler.py lines 504-518
-- ============================================
CREATE TABLE links (
  id UUID PRIMARY KEY,
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  source_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  target_url TEXT NOT NULL,
  is_internal BOOLEAN NOT NULL,
  depth INTEGER NOT NULL,
  status_code INTEGER,
  error TEXT,
  latency_ms INTEGER,
  anchor_text TEXT,
  is_nofollow BOOLEAN NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- ============================================
-- IMAGES TABLE - Exact schema from crawler.py lines 610-624
-- ============================================
CREATE TABLE images (
  id UUID PRIMARY KEY,
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  src TEXT NOT NULL,
  alt TEXT,
  title TEXT,
  width INTEGER,
  height INTEGER,
  has_alt BOOLEAN NOT NULL,
  is_broken BOOLEAN NOT NULL,
  status_code INTEGER,
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- ============================================
-- RLS POLICIES
-- ============================================
ALTER TABLE links ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

-- Service role policies (bypass RLS for Celery)
CREATE POLICY "Service role can insert pages" ON pages FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update pages" ON pages FOR UPDATE USING (true);
CREATE POLICY "Service role can select pages" ON pages FOR SELECT USING (true);

CREATE POLICY "Service role can insert links" ON links FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update links" ON links FOR UPDATE USING (true);
CREATE POLICY "Service role can select links" ON links FOR SELECT USING (true);

CREATE POLICY "Service role can insert images" ON images FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role can update images" ON images FOR UPDATE USING (true);
CREATE POLICY "Service role can select images" ON images FOR SELECT USING (true);

-- User policies
CREATE POLICY "Users can view their own links" ON links
  FOR SELECT
  USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = links.crawl_id AND crawls.user_id = auth.uid()));

CREATE POLICY "Users can view their own images" ON images
  FOR SELECT
  USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = images.crawl_id AND crawls.user_id = auth.uid()));

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX idx_links_crawl_id ON links(crawl_id);
CREATE INDEX idx_links_target_url ON links(crawl_id, target_url);
CREATE INDEX idx_links_depth ON links(crawl_id, depth);
CREATE INDEX idx_links_is_internal ON links(crawl_id, is_internal);
CREATE INDEX idx_images_crawl_id ON images(crawl_id);
CREATE INDEX idx_images_page_id ON images(page_id);
CREATE INDEX idx_images_src ON images(crawl_id, src);
