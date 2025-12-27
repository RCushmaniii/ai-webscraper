-- ============================================
-- COMPLETE DATABASE FIX
-- Run this ONCE and you're done
-- ============================================

-- Add ALL potentially missing columns to crawls table
ALTER TABLE crawls ADD COLUMN IF NOT EXISTS concurrency INT NOT NULL DEFAULT 5;
ALTER TABLE crawls ADD COLUMN IF NOT EXISTS name TEXT;

-- Ensure all tables exist (from schema.sql)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'admin',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  final_url TEXT NOT NULL,
  status_code INT,
  method TEXT NOT NULL DEFAULT 'html',
  render_ms INT,
  content_hash TEXT,
  html_storage_path TEXT,
  text_excerpt TEXT,
  word_count INT,
  canonical_url TEXT,
  is_indexable BOOLEAN DEFAULT true,
  content_type TEXT,
  page_size_bytes INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS seo_metadata (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  title TEXT,
  title_length INT,
  meta_description TEXT,
  meta_description_length INT,
  h1 TEXT,
  h2 TEXT[],
  robots_meta TEXT,
  hreflang JSONB,
  canonical TEXT,
  og_tags JSONB,
  twitter_tags JSONB,
  json_ld JSONB,
  image_alt_missing_count INT DEFAULT 0,
  internal_links INT DEFAULT 0,
  external_links INT DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS links (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  source_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  target_url TEXT NOT NULL,
  is_internal BOOLEAN NOT NULL,
  depth INT NOT NULL,
  status_code INT,
  error TEXT,
  latency_ms INT,
  anchor_text TEXT,
  is_nofollow BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS issues (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  pointer TEXT,
  context TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS summaries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  summary TEXT NOT NULL,
  business_value TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS batches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  total_sites INT DEFAULT 0,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS batch_sites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  crawl_id UUID REFERENCES crawls(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID NOT NULL,
  details JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS google_places (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  place_id TEXT NOT NULL,
  name TEXT NOT NULL,
  address TEXT,
  rating NUMERIC(3,1),
  reviews_count INT,
  reviews JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add RLS policies for missing CRUD operations
ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can insert their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can update their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can delete their own crawls" ON crawls;

CREATE POLICY "Users can insert their own crawls" ON crawls FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own crawls" ON crawls FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own crawls" ON crawls FOR DELETE USING (auth.uid() = user_id);

-- Add complete RLS for all tables
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can insert pages" ON pages;
DROP POLICY IF EXISTS "Users can update pages" ON pages;
DROP POLICY IF EXISTS "Users can delete pages" ON pages;

CREATE POLICY "Users can insert pages" ON pages FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = pages.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can update pages" ON pages FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = pages.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can delete pages" ON pages FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = pages.crawl_id AND crawls.user_id = auth.uid()));

ALTER TABLE links ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can insert links" ON links;
DROP POLICY IF EXISTS "Users can update links" ON links;
DROP POLICY IF EXISTS "Users can delete links" ON links;

CREATE POLICY "Users can insert links" ON links FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = links.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can update links" ON links FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = links.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can delete links" ON links FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = links.crawl_id AND crawls.user_id = auth.uid()));

ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can insert issues" ON issues;
DROP POLICY IF EXISTS "Users can update issues" ON issues;
DROP POLICY IF EXISTS "Users can delete issues" ON issues;

CREATE POLICY "Users can insert issues" ON issues FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = issues.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can update issues" ON issues FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = issues.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can delete issues" ON issues FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = issues.crawl_id AND crawls.user_id = auth.uid()));

ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can insert summaries" ON summaries;
DROP POLICY IF EXISTS "Users can update summaries" ON summaries;
DROP POLICY IF EXISTS "Users can delete summaries" ON summaries;

CREATE POLICY "Users can insert summaries" ON summaries FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = summaries.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can update summaries" ON summaries FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = summaries.crawl_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can delete summaries" ON summaries FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = summaries.crawl_id AND crawls.user_id = auth.uid()));

ALTER TABLE seo_metadata ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can insert seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can update seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can delete seo_metadata" ON seo_metadata;

CREATE POLICY "Users can insert seo_metadata" ON seo_metadata FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM pages JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = seo_metadata.page_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can update seo_metadata" ON seo_metadata FOR UPDATE USING (EXISTS (SELECT 1 FROM pages JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = seo_metadata.page_id AND crawls.user_id = auth.uid()));
CREATE POLICY "Users can delete seo_metadata" ON seo_metadata FOR DELETE USING (EXISTS (SELECT 1 FROM pages JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = seo_metadata.page_id AND crawls.user_id = auth.uid()));

-- Create indexes if not exist
CREATE INDEX IF NOT EXISTS idx_crawls_user_id ON crawls(user_id);
CREATE INDEX IF NOT EXISTS idx_pages_crawl_id ON pages(crawl_id);
CREATE INDEX IF NOT EXISTS idx_links_crawl_id ON links(crawl_id);
CREATE INDEX IF NOT EXISTS idx_issues_crawl_id ON issues(crawl_id);
CREATE INDEX IF NOT EXISTS idx_summaries_crawl_id ON summaries(crawl_id);
CREATE INDEX IF NOT EXISTS idx_seo_metadata_page_id ON seo_metadata(page_id);

-- DONE - Verify
SELECT 'COMPLETE - Crawls table columns:' as status;
SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'crawls' ORDER BY ordinal_position;