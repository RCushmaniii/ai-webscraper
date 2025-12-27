-- Comprehensive RLS fix for all tables
-- This allows the backend (service role) to bypass RLS while keeping security for users

-- ============================================
-- USERS TABLE
-- ============================================
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can insert their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

CREATE POLICY "Users can view their own data" ON users
  FOR SELECT USING (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can insert their own data" ON users
  FOR INSERT WITH CHECK (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can update their own data" ON users
  FOR UPDATE USING (auth.uid() = id OR auth.jwt()->>'role' = 'service_role');

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- ============================================
-- CRAWLS TABLE
-- ============================================
DROP POLICY IF EXISTS "Users can view their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can insert their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can update their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can delete their own crawls" ON crawls;

CREATE POLICY "Users can view their own crawls" ON crawls
  FOR SELECT USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can insert their own crawls" ON crawls
  FOR INSERT WITH CHECK (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can update their own crawls" ON crawls
  FOR UPDATE USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can delete their own crawls" ON crawls
  FOR DELETE USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;

-- ============================================
-- PAGES TABLE
-- ============================================
DROP POLICY IF EXISTS "Users can view their own pages" ON pages;
DROP POLICY IF EXISTS "Users can insert pages" ON pages;
DROP POLICY IF EXISTS "Users can update pages" ON pages;
DROP POLICY IF EXISTS "Users can delete pages" ON pages;

CREATE POLICY "Users can view their own pages" ON pages
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can insert pages" ON pages
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can update pages" ON pages
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can delete pages" ON pages
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

ALTER TABLE pages ENABLE ROW LEVEL SECURITY;

-- ============================================
-- LINKS TABLE
-- ============================================
DROP POLICY IF EXISTS "Users can view their own links" ON links;
DROP POLICY IF EXISTS "Users can insert links" ON links;
DROP POLICY IF EXISTS "Users can update links" ON links;
DROP POLICY IF EXISTS "Users can delete links" ON links;

CREATE POLICY "Users can view their own links" ON links
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can insert links" ON links
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can update links" ON links
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can delete links" ON links
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

ALTER TABLE links ENABLE ROW LEVEL SECURITY;

-- ============================================
-- ISSUES TABLE
-- ============================================
DROP POLICY IF EXISTS "Users can view their own issues" ON issues;
DROP POLICY IF EXISTS "Users can insert issues" ON issues;
DROP POLICY IF EXISTS "Users can update issues" ON issues;
DROP POLICY IF EXISTS "Users can delete issues" ON issues;

CREATE POLICY "Users can view their own issues" ON issues
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can insert issues" ON issues
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can update issues" ON issues
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can delete issues" ON issues
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

ALTER TABLE issues ENABLE ROW LEVEL SECURITY;

-- ============================================
-- SEO_METADATA TABLE
-- ============================================
DROP POLICY IF EXISTS "Users can view their own seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can insert seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can update seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can delete seo_metadata" ON seo_metadata;

CREATE POLICY "Users can view their own seo_metadata" ON seo_metadata
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can insert seo_metadata" ON seo_metadata
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can update seo_metadata" ON seo_metadata
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can delete seo_metadata" ON seo_metadata
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

ALTER TABLE seo_metadata ENABLE ROW LEVEL SECURITY;

-- ============================================
-- SUMMARIES TABLE
-- ============================================
DROP POLICY IF EXISTS "Users can view their own summaries" ON summaries;
DROP POLICY IF EXISTS "Users can insert summaries" ON summaries;
DROP POLICY IF EXISTS "Users can update summaries" ON summaries;
DROP POLICY IF EXISTS "Users can delete summaries" ON summaries;

CREATE POLICY "Users can view their own summaries" ON summaries
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can insert summaries" ON summaries
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can update summaries" ON summaries
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

CREATE POLICY "Users can delete summaries" ON summaries
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
      AND (crawls.user_id = auth.uid() OR auth.jwt()->>'role' = 'service_role')
    ) OR auth.jwt()->>'role' = 'service_role'
  );

ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

-- ============================================
-- BATCHES TABLE (if exists)
-- ============================================
DROP POLICY IF EXISTS "Users can view their own batches" ON batches;
DROP POLICY IF EXISTS "Users can insert their own batches" ON batches;
DROP POLICY IF EXISTS "Users can update their own batches" ON batches;
DROP POLICY IF EXISTS "Users can delete their own batches" ON batches;

CREATE POLICY "Users can view their own batches" ON batches
  FOR SELECT USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can insert their own batches" ON batches
  FOR INSERT WITH CHECK (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can update their own batches" ON batches
  FOR UPDATE USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can delete their own batches" ON batches
  FOR DELETE USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
