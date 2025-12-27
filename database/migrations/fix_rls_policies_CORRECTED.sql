-- ============================================
-- PRODUCTION-READY RLS POLICIES
-- ============================================
-- Expert-reviewed and corrected RLS setup
--
-- KEY CHANGES FROM PREVIOUS VERSION:
-- ✅ Removed ALL service_role checks (service role bypasses RLS automatically)
-- ✅ Using auth.uid() only (no auth.jwt() overhead)
-- ✅ Clean ownership model through crawls table
-- ✅ Added foreign key constraints for data integrity
-- ✅ Added indexes for RLS query performance
--
-- IMPORTANT: Your backend using SUPABASE_SERVICE_ROLE_KEY will bypass ALL these policies.
-- These policies ONLY apply to anon/authenticated user requests.
-- ============================================

-- ============================================
-- PART 1: FOREIGN KEY CONSTRAINTS
-- Ensures referential integrity and safe cascading deletes
-- ============================================

-- Pages → Crawls
ALTER TABLE pages DROP CONSTRAINT IF EXISTS pages_crawl_id_fkey;
ALTER TABLE pages
ADD CONSTRAINT pages_crawl_id_fkey
FOREIGN KEY (crawl_id) REFERENCES crawls(id)
ON DELETE CASCADE;

-- Links → Crawls
ALTER TABLE links DROP CONSTRAINT IF EXISTS links_crawl_id_fkey;
ALTER TABLE links
ADD CONSTRAINT links_crawl_id_fkey
FOREIGN KEY (crawl_id) REFERENCES crawls(id)
ON DELETE CASCADE;

-- Issues → Crawls
ALTER TABLE issues DROP CONSTRAINT IF EXISTS issues_crawl_id_fkey;
ALTER TABLE issues
ADD CONSTRAINT issues_crawl_id_fkey
FOREIGN KEY (crawl_id) REFERENCES crawls(id)
ON DELETE CASCADE;

-- SEO Metadata → Pages
ALTER TABLE seo_metadata DROP CONSTRAINT IF EXISTS seo_metadata_page_id_fkey;
ALTER TABLE seo_metadata
ADD CONSTRAINT seo_metadata_page_id_fkey
FOREIGN KEY (page_id) REFERENCES pages(id)
ON DELETE CASCADE;

-- Summaries → Crawls
ALTER TABLE summaries DROP CONSTRAINT IF EXISTS summaries_crawl_id_fkey;
ALTER TABLE summaries
ADD CONSTRAINT summaries_crawl_id_fkey
FOREIGN KEY (crawl_id) REFERENCES crawls(id)
ON DELETE CASCADE;

-- Crawls → Users
ALTER TABLE crawls DROP CONSTRAINT IF EXISTS crawls_user_id_fkey;
ALTER TABLE crawls
ADD CONSTRAINT crawls_user_id_fkey
FOREIGN KEY (user_id) REFERENCES auth.users(id)
ON DELETE CASCADE;

-- Batches → Users (if batches table exists)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'batches') THEN
    ALTER TABLE batches DROP CONSTRAINT IF EXISTS batches_user_id_fkey;
    ALTER TABLE batches
    ADD CONSTRAINT batches_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES auth.users(id)
    ON DELETE CASCADE;
  END IF;
END $$;

-- ============================================
-- PART 2: PERFORMANCE INDEXES
-- Critical for RLS query performance at scale
-- ============================================

-- Crawls table indexes
CREATE INDEX IF NOT EXISTS idx_crawls_user_id ON crawls(user_id);
CREATE INDEX IF NOT EXISTS idx_crawls_id_user_id ON crawls(id, user_id);

-- Pages table indexes
CREATE INDEX IF NOT EXISTS idx_pages_crawl_id ON pages(crawl_id);

-- Links table indexes
CREATE INDEX IF NOT EXISTS idx_links_crawl_id ON links(crawl_id);

-- Issues table indexes
CREATE INDEX IF NOT EXISTS idx_issues_crawl_id ON issues(crawl_id);

-- SEO Metadata table indexes
CREATE INDEX IF NOT EXISTS idx_seo_metadata_page_id ON seo_metadata(page_id);

-- Summaries table indexes
CREATE INDEX IF NOT EXISTS idx_summaries_crawl_id ON summaries(crawl_id);

-- Batches table indexes (if exists)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'batches') THEN
    CREATE INDEX IF NOT EXISTS idx_batches_user_id ON batches(user_id);
  END IF;
END $$;

-- ============================================
-- PART 3: RLS POLICIES
-- Clean, simple, and correct
-- ============================================

-- --------------------------------------------
-- USERS TABLE
-- --------------------------------------------
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can insert their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

CREATE POLICY "Users can view their own data" ON users
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can insert their own data" ON users
  FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own data" ON users
  FOR UPDATE
  USING (auth.uid() = id);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------
-- CRAWLS TABLE
-- --------------------------------------------
DROP POLICY IF EXISTS "Users can view their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can insert their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can update their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can delete their own crawls" ON crawls;

CREATE POLICY "Users can view their own crawls" ON crawls
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own crawls" ON crawls
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own crawls" ON crawls
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own crawls" ON crawls
  FOR DELETE
  USING (auth.uid() = user_id);

ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------
-- PAGES TABLE
-- --------------------------------------------
DROP POLICY IF EXISTS "Users can view their own pages" ON pages;
DROP POLICY IF EXISTS "Users can insert pages" ON pages;
DROP POLICY IF EXISTS "Users can update pages" ON pages;
DROP POLICY IF EXISTS "Users can delete pages" ON pages;

CREATE POLICY "Users can view their own pages" ON pages
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert pages" ON pages
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update pages" ON pages
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete pages" ON pages
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

ALTER TABLE pages ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------
-- LINKS TABLE
-- --------------------------------------------
DROP POLICY IF EXISTS "Users can view their own links" ON links;
DROP POLICY IF EXISTS "Users can insert links" ON links;
DROP POLICY IF EXISTS "Users can update links" ON links;
DROP POLICY IF EXISTS "Users can delete links" ON links;

CREATE POLICY "Users can view their own links" ON links
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert links" ON links
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update links" ON links
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete links" ON links
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

ALTER TABLE links ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------
-- ISSUES TABLE
-- --------------------------------------------
DROP POLICY IF EXISTS "Users can view their own issues" ON issues;
DROP POLICY IF EXISTS "Users can insert issues" ON issues;
DROP POLICY IF EXISTS "Users can update issues" ON issues;
DROP POLICY IF EXISTS "Users can delete issues" ON issues;

CREATE POLICY "Users can view their own issues" ON issues
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert issues" ON issues
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update issues" ON issues
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete issues" ON issues
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

ALTER TABLE issues ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------
-- SEO_METADATA TABLE
-- --------------------------------------------
DROP POLICY IF EXISTS "Users can view their own seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can insert seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can update seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can delete seo_metadata" ON seo_metadata;

CREATE POLICY "Users can view their own seo_metadata" ON seo_metadata
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert seo_metadata" ON seo_metadata
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update seo_metadata" ON seo_metadata
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete seo_metadata" ON seo_metadata
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM pages
      JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
        AND crawls.user_id = auth.uid()
    )
  );

ALTER TABLE seo_metadata ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------
-- SUMMARIES TABLE
-- --------------------------------------------
DROP POLICY IF EXISTS "Users can view their own summaries" ON summaries;
DROP POLICY IF EXISTS "Users can insert summaries" ON summaries;
DROP POLICY IF EXISTS "Users can update summaries" ON summaries;
DROP POLICY IF EXISTS "Users can delete summaries" ON summaries;

CREATE POLICY "Users can view their own summaries" ON summaries
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert summaries" ON summaries
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update summaries" ON summaries
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete summaries" ON summaries
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
        AND crawls.user_id = auth.uid()
    )
  );

ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------
-- BATCHES TABLE (if exists)
-- --------------------------------------------
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'batches') THEN
    DROP POLICY IF EXISTS "Users can view their own batches" ON batches;
    DROP POLICY IF EXISTS "Users can insert their own batches" ON batches;
    DROP POLICY IF EXISTS "Users can update their own batches" ON batches;
    DROP POLICY IF EXISTS "Users can delete their own batches" ON batches;

    CREATE POLICY "Users can view their own batches" ON batches
      FOR SELECT
      USING (auth.uid() = user_id);

    CREATE POLICY "Users can insert their own batches" ON batches
      FOR INSERT
      WITH CHECK (auth.uid() = user_id);

    CREATE POLICY "Users can update their own batches" ON batches
      FOR UPDATE
      USING (auth.uid() = user_id);

    CREATE POLICY "Users can delete their own batches" ON batches
      FOR DELETE
      USING (auth.uid() = user_id);

    ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

-- ============================================
-- VERIFICATION QUERIES
-- Run these after migration to verify RLS is working
-- ============================================

-- Check all tables have RLS enabled
SELECT
  schemaname,
  tablename,
  rowsecurity
FROM pg_tables
WHERE tablename IN ('users', 'crawls', 'pages', 'links', 'issues', 'seo_metadata', 'summaries', 'batches')
ORDER BY tablename;

-- Check all policies exist
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd
FROM pg_policies
WHERE tablename IN ('users', 'crawls', 'pages', 'links', 'issues', 'seo_metadata', 'summaries', 'batches')
ORDER BY tablename, policyname;

-- Check foreign keys
SELECT
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('crawls', 'pages', 'links', 'issues', 'seo_metadata', 'summaries', 'batches')
ORDER BY tc.table_name;

-- Check indexes
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename IN ('crawls', 'pages', 'links', 'issues', 'seo_metadata', 'summaries', 'batches')
ORDER BY tablename, indexname;