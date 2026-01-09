-- ============================================
-- COMPLETE SCHEMA FIX FOR CELERY CRAWLER
-- This migration adds all missing columns that the crawler needs
-- ============================================

-- ===========================================
-- FIX 1: Update PAGES table with missing columns
-- ===========================================

-- Add missing columns to pages table
ALTER TABLE pages
ADD COLUMN IF NOT EXISTS final_url TEXT,
ADD COLUMN IF NOT EXISTS method TEXT,
ADD COLUMN IF NOT EXISTS render_ms INTEGER,
ADD COLUMN IF NOT EXISTS content_hash TEXT,
ADD COLUMN IF NOT EXISTS html_storage_path TEXT,
ADD COLUMN IF NOT EXISTS text_excerpt TEXT,
ADD COLUMN IF NOT EXISTS full_content TEXT,
ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS page_size_bytes INTEGER DEFAULT 0;

-- Update existing response_time to match render_ms if needed
UPDATE pages SET render_ms = response_time WHERE render_ms IS NULL AND response_time IS NOT NULL;

-- Update existing content_length to match page_size_bytes if needed
UPDATE pages SET page_size_bytes = content_length WHERE page_size_bytes = 0 AND content_length IS NOT NULL;

-- ===========================================
-- FIX 2: Recreate LINKS table with correct schema
-- ===========================================

-- Drop old links table and recreate with correct schema
DROP TABLE IF EXISTS links CASCADE;

CREATE TABLE links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  source_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  target_url TEXT NOT NULL,
  is_internal BOOLEAN NOT NULL DEFAULT false,
  depth INTEGER NOT NULL DEFAULT 0,
  status_code INTEGER,
  error TEXT,
  latency_ms INTEGER,
  anchor_text TEXT,
  is_nofollow BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE links ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for links
CREATE POLICY "Users can view links from own crawls" ON links
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert links" ON links
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update links" ON links
  FOR UPDATE USING (true);

CREATE POLICY "Service role can select links" ON links
  FOR SELECT USING (true);

-- Create indexes
CREATE INDEX idx_links_crawl_id ON links(crawl_id);
CREATE INDEX idx_links_source_page_id ON links(source_page_id);
CREATE INDEX idx_links_target_url ON links(crawl_id, target_url);

-- ===========================================
-- FIX 3: Create IMAGES table
-- ===========================================

-- Drop if exists and create fresh
DROP TABLE IF EXISTS images CASCADE;

CREATE TABLE images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  src TEXT NOT NULL,
  alt TEXT,
  title TEXT,
  width INTEGER,
  height INTEGER,
  has_alt BOOLEAN NOT NULL DEFAULT false,
  is_broken BOOLEAN NOT NULL DEFAULT false,
  status_code INTEGER,
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for images
CREATE POLICY "Users can view images from own crawls" ON images
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = images.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert images" ON images
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update images" ON images
  FOR UPDATE USING (true);

CREATE POLICY "Service role can select images" ON images
  FOR SELECT USING (true);

-- Create indexes
CREATE INDEX idx_images_crawl_id ON images(crawl_id);
CREATE INDEX idx_images_page_id ON images(page_id);

-- ===========================================
-- FIX 4: Create SEO_AUDITS table
-- ===========================================

DROP TABLE IF EXISTS seo_audits CASCADE;

CREATE TABLE seo_audits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  title_issues TEXT[] DEFAULT '{}',
  meta_description_issues TEXT[] DEFAULT '{}',
  heading_issues TEXT[] DEFAULT '{}',
  image_issues TEXT[] DEFAULT '{}',
  content_quality_score INTEGER DEFAULT 0,
  seo_score INTEGER DEFAULT 0,
  technical_issues TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE seo_audits ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view SEO audits from own crawls" ON seo_audits
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = seo_audits.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert SEO audits" ON seo_audits
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update SEO audits" ON seo_audits
  FOR UPDATE USING (true);

CREATE POLICY "Service role can select SEO audits" ON seo_audits
  FOR SELECT USING (true);

-- Create indexes
CREATE INDEX idx_seo_audits_crawl_id ON seo_audits(crawl_id);
CREATE INDEX idx_seo_audits_page_id ON seo_audits(page_id);

-- ===========================================
-- FIX 5: Create/Update ISSUES table
-- ===========================================

DROP TABLE IF EXISTS issues CASCADE;

CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'error')),
  message TEXT NOT NULL,
  pointer TEXT,
  context TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view issues from own crawls" ON issues
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can insert issues" ON issues
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update issues" ON issues
  FOR UPDATE USING (true);

CREATE POLICY "Service role can select issues" ON issues
  FOR SELECT USING (true);

-- Create indexes
CREATE INDEX idx_issues_crawl_id ON issues(crawl_id);
CREATE INDEX idx_issues_page_id ON issues(page_id);
CREATE INDEX idx_issues_severity ON issues(severity);

-- ===========================================
-- FIX 6: Add missing columns to CRAWLS table
-- ===========================================

ALTER TABLE crawls
ADD COLUMN IF NOT EXISTS internal_depth INTEGER DEFAULT 2,
ADD COLUMN IF NOT EXISTS external_depth INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS follow_external BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS max_runtime_sec INTEGER DEFAULT 3600;

-- ===========================================
-- FIX 7: Create triggers for updated_at
-- ===========================================

-- Ensure we have the trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for new tables
DROP TRIGGER IF EXISTS update_links_updated_at ON links;
CREATE TRIGGER update_links_updated_at BEFORE UPDATE ON links
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_images_updated_at ON images;
CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON images
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_seo_audits_updated_at ON seo_audits;
CREATE TRIGGER update_seo_audits_updated_at BEFORE UPDATE ON seo_audits
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_issues_updated_at ON issues;
CREATE TRIGGER update_issues_updated_at BEFORE UPDATE ON issues
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- VERIFICATION
-- ===========================================

-- Show all tables and their column counts
SELECT
  tablename,
  (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = tablename) as column_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;