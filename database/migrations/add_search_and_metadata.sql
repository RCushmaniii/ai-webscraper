-- Phase 1: Enhanced Search & Filtering - Database Schema
-- Add full-text search indexes for pages
CREATE INDEX IF NOT EXISTS idx_pages_title_search ON pages USING gin(to_tsvector('english', COALESCE(title, '')));
CREATE INDEX IF NOT EXISTS idx_pages_content_search ON pages USING gin(to_tsvector('english', COALESCE(content_summary, '')));

-- Add metadata columns for flagging and review
ALTER TABLE pages ADD COLUMN IF NOT EXISTS is_flagged BOOLEAN DEFAULT false;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS notes TEXT;

-- Add columns for broken link tracking (if they don't exist)
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_broken BOOLEAN DEFAULT false;

-- Add indexes for filtering
CREATE INDEX IF NOT EXISTS idx_pages_status_code ON pages(crawl_id, status_code);
CREATE INDEX IF NOT EXISTS idx_pages_flagged ON pages(crawl_id, is_flagged);
CREATE INDEX IF NOT EXISTS idx_links_status ON links(crawl_id, status_code);
CREATE INDEX IF NOT EXISTS idx_links_broken ON links(crawl_id, is_broken);
CREATE INDEX IF NOT EXISTS idx_images_broken ON images(crawl_id, is_broken);
CREATE INDEX IF NOT EXISTS idx_images_has_alt ON images(crawl_id, has_alt);

-- Phase 2: Page Categorization & Metadata
ALTER TABLE pages ADD COLUMN IF NOT EXISTS page_type TEXT; -- 'nav', 'footer', 'landing', 'blog', 'product', 'other'
ALTER TABLE pages ADD COLUMN IF NOT EXISTS is_in_navigation BOOLEAN DEFAULT false;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS is_in_footer BOOLEAN DEFAULT false;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS parent_page_id UUID REFERENCES pages(id) ON DELETE SET NULL;

-- Add indexes for page type filtering
CREATE INDEX IF NOT EXISTS idx_pages_type ON pages(crawl_id, page_type);
CREATE INDEX IF NOT EXISTS idx_pages_navigation ON pages(crawl_id, is_in_navigation);
CREATE INDEX IF NOT EXISTS idx_pages_footer ON pages(crawl_id, is_in_footer);
CREATE INDEX IF NOT EXISTS idx_pages_parent ON pages(parent_page_id);

-- Phase 3: Site Structure Visualization
CREATE TABLE IF NOT EXISTS site_structure (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  parent_page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  depth INTEGER NOT NULL,
  path TEXT[], -- Array of page IDs from root
  children_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_site_structure_crawl ON site_structure(crawl_id);
CREATE INDEX IF NOT EXISTS idx_site_structure_page ON site_structure(page_id);
CREATE INDEX IF NOT EXISTS idx_site_structure_parent ON site_structure(parent_page_id);
CREATE INDEX IF NOT EXISTS idx_site_structure_depth ON site_structure(crawl_id, depth);

-- Add helpful comments
COMMENT ON COLUMN pages.is_flagged IS 'User flag for pages needing review';
COMMENT ON COLUMN pages.reviewed_at IS 'Timestamp when page was last reviewed';
COMMENT ON COLUMN pages.notes IS 'User notes about this page';
COMMENT ON COLUMN pages.page_type IS 'Auto-detected page type: nav, footer, landing, blog, product, other';
COMMENT ON COLUMN pages.is_in_navigation IS 'True if page appears in main navigation';
COMMENT ON COLUMN pages.is_in_footer IS 'True if page appears in footer';
COMMENT ON COLUMN pages.parent_page_id IS 'Parent page in site hierarchy';
COMMENT ON TABLE site_structure IS 'Stores hierarchical site structure for visualization';
