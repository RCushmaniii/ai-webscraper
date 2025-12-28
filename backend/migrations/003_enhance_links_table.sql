-- Migration: Enhance links table with comprehensive metadata
-- Date: 2025-01-XX
-- Description: Adds enhanced fields for link analysis and SEO insights

-- Add new columns to existing links table
ALTER TABLE links ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS target_url_normalized TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS anchor_text_length INTEGER;
ALTER TABLE links ADD COLUMN IF NOT EXISTS rel_attributes TEXT[];
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_image_link BOOLEAN DEFAULT FALSE;
ALTER TABLE links ADD COLUMN IF NOT EXISTS link_position VARCHAR(20);
ALTER TABLE links ADD COLUMN IF NOT EXISTS dom_depth INTEGER;
ALTER TABLE links ADD COLUMN IF NOT EXISTS redirect_chain JSONB;
ALTER TABLE links ADD COLUMN IF NOT EXISTS redirect_count INTEGER DEFAULT 0;
ALTER TABLE links ADD COLUMN IF NOT EXISTS final_url TEXT;
ALTER TABLE links ADD COLUMN IF NOT EXISTS has_generic_anchor BOOLEAN DEFAULT FALSE;
ALTER TABLE links ADD COLUMN IF NOT EXISTS has_empty_anchor BOOLEAN DEFAULT FALSE;
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_orphan_creator BOOLEAN DEFAULT FALSE;
ALTER TABLE links ADD COLUMN IF NOT EXISTS checked_at TIMESTAMPTZ;

-- Rename existing column for consistency
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'links' AND column_name = 'status_code') THEN
        ALTER TABLE links RENAME COLUMN status_code TO http_status;
    END IF;
END $$;

-- Update anchor_text_length from existing anchor_text
UPDATE links SET anchor_text_length = LENGTH(anchor_text) WHERE anchor_text IS NOT NULL;

-- Update has_empty_anchor flag
UPDATE links SET has_empty_anchor = TRUE WHERE anchor_text IS NULL OR TRIM(anchor_text) = '';

-- Create additional indexes for enhanced queries
CREATE INDEX IF NOT EXISTS idx_links_target_normalized ON links(crawl_id, target_url_normalized);
CREATE INDEX IF NOT EXISTS idx_links_position ON links(crawl_id, link_position);
CREATE INDEX IF NOT EXISTS idx_links_generic_anchor ON links(crawl_id) WHERE has_generic_anchor = TRUE;
CREATE INDEX IF NOT EXISTS idx_links_empty_anchor ON links(crawl_id) WHERE has_empty_anchor = TRUE;
CREATE INDEX IF NOT EXISTS idx_links_redirects ON links(crawl_id) WHERE redirect_count > 0;

-- Create page_link_metrics table for aggregated analysis
CREATE TABLE IF NOT EXISTS page_link_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,

    -- Outbound metrics
    internal_links_out INTEGER DEFAULT 0,
    external_links_out INTEGER DEFAULT 0,
    broken_links_out INTEGER DEFAULT 0,

    -- Inbound metrics
    internal_links_in INTEGER DEFAULT 0,
    unique_pages_linking INTEGER DEFAULT 0,

    -- Derived metrics
    is_orphan BOOLEAN DEFAULT FALSE,
    is_dead_end BOOLEAN DEFAULT FALSE,
    link_depth INTEGER,

    -- Anchor analysis
    generic_anchor_count INTEGER DEFAULT 0,
    unique_anchors_in JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(page_id, crawl_id)
);

-- Enable RLS on page_link_metrics
ALTER TABLE page_link_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own page_link_metrics" ON page_link_metrics
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = page_link_metrics.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Create indexes for page_link_metrics
CREATE INDEX IF NOT EXISTS idx_page_link_metrics_page_id ON page_link_metrics(page_id);
CREATE INDEX IF NOT EXISTS idx_page_link_metrics_crawl_id ON page_link_metrics(crawl_id);
CREATE INDEX IF NOT EXISTS idx_page_link_metrics_orphans ON page_link_metrics(crawl_id) WHERE is_orphan = TRUE;
CREATE INDEX IF NOT EXISTS idx_page_link_metrics_dead_ends ON page_link_metrics(crawl_id) WHERE is_dead_end = TRUE;

-- Add comments
COMMENT ON COLUMN links.source_url IS 'URL of the page containing this link';
COMMENT ON COLUMN links.target_url_normalized IS 'Normalized target URL for deduplication';
COMMENT ON COLUMN links.link_position IS 'Location in page: navigation, content, footer, sidebar';
COMMENT ON COLUMN links.rel_attributes IS 'Array of rel attribute values (nofollow, sponsored, etc.)';
COMMENT ON COLUMN links.redirect_chain IS 'JSON array of redirect hops';
COMMENT ON COLUMN links.has_generic_anchor IS 'True if anchor text is generic (click here, read more, etc.)';
COMMENT ON TABLE page_link_metrics IS 'Aggregated link metrics per page for fast analytics';
