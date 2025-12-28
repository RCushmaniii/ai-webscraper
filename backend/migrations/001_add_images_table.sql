-- Migration: Add images table for storing extracted images from crawled pages
-- Date: 2025-01-XX
-- Description: Creates images table to store image metadata extracted during crawls

-- Create images table
CREATE TABLE IF NOT EXISTS images (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  src TEXT NOT NULL,
  alt TEXT,
  title TEXT,
  width INT,
  height INT,
  has_alt BOOLEAN DEFAULT false,
  is_broken BOOLEAN DEFAULT false,
  status_code INT,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

-- Create RLS policy: Users can only view images from their own crawls
CREATE POLICY "Users can view their own images" ON images
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = images.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_crawl_id ON images(crawl_id);
CREATE INDEX IF NOT EXISTS idx_images_page_id ON images(page_id);
CREATE INDEX IF NOT EXISTS idx_images_is_broken ON images(is_broken);
CREATE INDEX IF NOT EXISTS idx_images_has_alt ON images(has_alt);

-- Add comment
COMMENT ON TABLE images IS 'Stores metadata for images extracted from crawled pages';