-- Migration: Add full_content column to pages table
-- Date: 2025-01-XX
-- Description: Adds full_content column to store complete page text (not truncated)

-- Add full_content column to pages table
ALTER TABLE pages ADD COLUMN IF NOT EXISTS full_content TEXT;

-- Create GIN index for full-text search on full_content
CREATE INDEX IF NOT EXISTS idx_pages_full_content_fts
  ON pages USING gin(to_tsvector('english', COALESCE(full_content, '')));

-- Add comment
COMMENT ON COLUMN pages.full_content IS 'Complete extracted text content from page (not truncated)';