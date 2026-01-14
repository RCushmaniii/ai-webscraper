-- Migration: Add html_snapshot_path column to pages table
-- Version: 015
-- Description: Store path to HTML snapshot file for full content retrieval
-- Date: 2026-01-12

-- Add html_snapshot_path column to store the file path
ALTER TABLE pages ADD COLUMN IF NOT EXISTS html_snapshot_path TEXT;

-- Add index for faster lookups when retrieving HTML content
CREATE INDEX IF NOT EXISTS idx_pages_html_snapshot_path ON pages(html_snapshot_path) WHERE html_snapshot_path IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN pages.html_snapshot_path IS 'File path to stored HTML snapshot for full content retrieval';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
