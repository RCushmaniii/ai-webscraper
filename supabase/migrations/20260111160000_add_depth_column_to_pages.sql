-- Migration: Add depth column to pages table
-- Version: 014
-- Description: Add missing depth column for crawl depth tracking
-- Date: 2026-01-11

-- Add depth column if it doesn't exist
ALTER TABLE pages ADD COLUMN IF NOT EXISTS depth INT NOT NULL DEFAULT 0;

-- Add comment for documentation
COMMENT ON COLUMN pages.depth IS 'Crawl depth: 0 = starting URL, 1 = linked from start, etc.';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
