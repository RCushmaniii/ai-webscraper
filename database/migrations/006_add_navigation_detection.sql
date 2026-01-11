-- Migration: Add Navigation Detection Fields to Links Table
-- Version: 006
-- Description: Adds fields to track navigation link detection scores
-- Date: 2026-01-10

-- Add navigation detection columns to links table
ALTER TABLE links ADD COLUMN IF NOT EXISTS nav_score INTEGER DEFAULT 0;
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_navigation BOOLEAN DEFAULT FALSE;

-- Add index for filtering navigation links
CREATE INDEX IF NOT EXISTS idx_links_is_navigation ON links(is_navigation) WHERE is_navigation = TRUE;
CREATE INDEX IF NOT EXISTS idx_links_nav_score ON links(nav_score) WHERE nav_score > 0;

-- Add comments explaining the fields
COMMENT ON COLUMN links.nav_score IS 'Navigation importance score (0-20+). Higher = more likely main navigation. Based on HTML location (nav, header, footer) and class names.';
COMMENT ON COLUMN links.is_navigation IS 'TRUE if link is identified as main navigation (nav_score >= 8 or in primary nav detection).';

-- Also add is_primary field to pages table for pages identified as primary navigation targets
ALTER TABLE pages ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS nav_score INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_pages_is_primary ON pages(is_primary) WHERE is_primary = TRUE;

COMMENT ON COLUMN pages.is_primary IS 'TRUE if this page was identified as a primary navigation target (About, Contact, Services, etc.)';
COMMENT ON COLUMN pages.nav_score IS 'Navigation score inherited from the link that led to this page.';
