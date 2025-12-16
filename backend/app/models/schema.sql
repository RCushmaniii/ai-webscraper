-- Database schema for AAA Web Scraper Platform

-- Enable Row Level Security
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

-- Users table (mirrors Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY REFERENCES auth.users,
  email TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'admin',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own data" ON users
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Only admins can insert" ON users
  FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Only admins can update" ON users
  FOR UPDATE USING (auth.jwt() ->> 'role' = 'admin');

-- Crawls table
CREATE TABLE IF NOT EXISTS crawls (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  start_url TEXT NOT NULL,
  internal_depth INT NOT NULL DEFAULT 2,
  follow_external BOOLEAN NOT NULL DEFAULT false,
  external_depth INT NOT NULL DEFAULT 0,
  max_pages INT NOT NULL DEFAULT 100,
  max_runtime_sec INT NOT NULL DEFAULT 3600,
  concurrency INT NOT NULL DEFAULT 5,
  rate_limit_rps NUMERIC(5,2) NOT NULL DEFAULT 2.0,
  user_agent_profile TEXT NOT NULL DEFAULT 'standard',
  robots_policy TEXT NOT NULL DEFAULT 'respect',
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  total_pages INT DEFAULT 0,
  notes TEXT,
  config_snapshot JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS on crawls table
ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own crawls" ON crawls
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own crawls" ON crawls
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own crawls" ON crawls
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own crawls" ON crawls
  FOR DELETE USING (auth.uid() = user_id);

-- Pages table
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

-- Enable RLS on pages table
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own pages" ON pages
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- SEO metadata table
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

-- Enable RLS on seo_metadata table
ALTER TABLE seo_metadata ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own seo_metadata" ON seo_metadata
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Links table
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

-- Enable RLS on links table
ALTER TABLE links ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own links" ON links
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Issues table
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

-- Enable RLS on issues table
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own issues" ON issues
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Summaries table
CREATE TABLE IF NOT EXISTS summaries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  summary TEXT NOT NULL,
  business_value TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS on summaries table
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own summaries" ON summaries
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Batch jobs table
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

-- Enable RLS on batches table
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own batches" ON batches
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own batches" ON batches
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own batches" ON batches
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own batches" ON batches
  FOR DELETE USING (auth.uid() = user_id);

-- Batch sites table
CREATE TABLE IF NOT EXISTS batch_sites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  crawl_id UUID REFERENCES crawls(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS on batch_sites table
ALTER TABLE batch_sites ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own batch_sites" ON batch_sites
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM batches
      WHERE batches.id = batch_sites.batch_id
      AND batches.user_id = auth.uid()
    )
  );

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID NOT NULL,
  details JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS on audit_log table
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own audit_log" ON audit_log
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own audit_log" ON audit_log
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Google Places table
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

-- Enable RLS on google_places table
ALTER TABLE google_places ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own google_places" ON google_places
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own google_places" ON google_places
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own google_places" ON google_places
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own google_places" ON google_places
  FOR DELETE USING (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_crawls_user_id ON crawls(user_id);
CREATE INDEX IF NOT EXISTS idx_pages_crawl_id ON pages(crawl_id);
CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url);
CREATE INDEX IF NOT EXISTS idx_seo_metadata_page_id ON seo_metadata(page_id);
CREATE INDEX IF NOT EXISTS idx_links_crawl_id ON links(crawl_id);
CREATE INDEX IF NOT EXISTS idx_links_source_page_id ON links(source_page_id);
CREATE INDEX IF NOT EXISTS idx_issues_crawl_id ON issues(crawl_id);
CREATE INDEX IF NOT EXISTS idx_issues_page_id ON issues(page_id);
CREATE INDEX IF NOT EXISTS idx_summaries_page_id ON summaries(page_id);
CREATE INDEX IF NOT EXISTS idx_summaries_crawl_id ON summaries(crawl_id);
CREATE INDEX IF NOT EXISTS idx_batches_user_id ON batches(user_id);
CREATE INDEX IF NOT EXISTS idx_batch_sites_batch_id ON batch_sites(batch_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_google_places_user_id ON google_places(user_id);
