-- Migration: Fix RLS Auth Performance (Auth RLS Initialization Plan)
-- Version: 009
-- Description: Wrap auth.uid() and auth.role() in subqueries to prevent per-row re-evaluation
-- Date: 2026-01-11
--
-- ISSUE: Supabase lint warning "Auth RLS Initialization Plan"
-- Current:  auth.uid() = user_id  (re-evaluated per row - slow at scale)
-- Fixed:    (select auth.uid()) = user_id  (evaluated once per statement - fast)
--
-- Affected tables:
--   users, crawls, pages, links, images, seo_metadata, issues, summaries,
--   site_structure, batches, batch_sites
--
-- ============================================================================

-- ============================================================================
-- PART 1: USERS TABLE
-- ============================================================================

DROP POLICY IF EXISTS "users_select_own" ON users;
DROP POLICY IF EXISTS "users_insert_own" ON users;
DROP POLICY IF EXISTS "users_update_own" ON users;
DROP POLICY IF EXISTS "users_delete_own" ON users;

CREATE POLICY "users_select_own"
  ON users FOR SELECT
  USING ((select auth.uid()) = id);

CREATE POLICY "users_insert_own"
  ON users FOR INSERT
  WITH CHECK ((select auth.uid()) = id);

CREATE POLICY "users_update_own"
  ON users FOR UPDATE
  USING ((select auth.uid()) = id)
  WITH CHECK ((select auth.uid()) = id);

CREATE POLICY "users_delete_own"
  ON users FOR DELETE
  USING ((select auth.uid()) = id);

-- ============================================================================
-- PART 2: CRAWLS TABLE
-- ============================================================================

DROP POLICY IF EXISTS "crawls_select_own" ON crawls;
DROP POLICY IF EXISTS "crawls_insert_own" ON crawls;
DROP POLICY IF EXISTS "crawls_update_own" ON crawls;
DROP POLICY IF EXISTS "crawls_delete_own" ON crawls;
DROP POLICY IF EXISTS "Users can view their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can insert their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can update their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can delete their own crawls" ON crawls;

CREATE POLICY "crawls_select_own"
  ON crawls FOR SELECT
  USING ((select auth.uid()) = user_id);

CREATE POLICY "crawls_insert_own"
  ON crawls FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "crawls_update_own"
  ON crawls FOR UPDATE
  USING ((select auth.uid()) = user_id)
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "crawls_delete_own"
  ON crawls FOR DELETE
  USING ((select auth.uid()) = user_id);

-- ============================================================================
-- PART 3: PAGES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "pages_select_own" ON pages;
DROP POLICY IF EXISTS "Users can view their own pages" ON pages;

CREATE POLICY "pages_select_own"
  ON pages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
      AND crawls.user_id = (select auth.uid())
    )
  );

-- ============================================================================
-- PART 4: LINKS TABLE
-- ============================================================================

DROP POLICY IF EXISTS "links_select_own" ON links;
DROP POLICY IF EXISTS "Users can view their own links" ON links;

CREATE POLICY "links_select_own"
  ON links FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
      AND crawls.user_id = (select auth.uid())
    )
  );

-- ============================================================================
-- PART 5: IMAGES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "images_select_own" ON images;
DROP POLICY IF EXISTS "Users can view their own images" ON images;

CREATE POLICY "images_select_own"
  ON images FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = images.crawl_id
      AND crawls.user_id = (select auth.uid())
    )
  );

-- ============================================================================
-- PART 6: SEO_METADATA TABLE
-- ============================================================================

DROP POLICY IF EXISTS "seo_metadata_select_own" ON seo_metadata;
DROP POLICY IF EXISTS "Users can view their own seo_metadata" ON seo_metadata;

CREATE POLICY "seo_metadata_select_own"
  ON seo_metadata FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM pages
      INNER JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
      AND crawls.user_id = (select auth.uid())
    )
  );

-- ============================================================================
-- PART 7: ISSUES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "issues_select_own" ON issues;
DROP POLICY IF EXISTS "Users can view their own issues" ON issues;

CREATE POLICY "issues_select_own"
  ON issues FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
      AND crawls.user_id = (select auth.uid())
    )
  );

-- ============================================================================
-- PART 8: SUMMARIES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "summaries_select_own" ON summaries;
DROP POLICY IF EXISTS "Users can view their own summaries" ON summaries;

CREATE POLICY "summaries_select_own"
  ON summaries FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
      AND crawls.user_id = (select auth.uid())
    )
  );

-- ============================================================================
-- PART 9: SITE_STRUCTURE TABLE
-- ============================================================================

DROP POLICY IF EXISTS "Users can view own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Users can insert own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Users can update own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Users can delete own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Service role full access to site_structure" ON site_structure;

CREATE POLICY "Users can view own site_structure"
  ON site_structure FOR SELECT
  USING (crawl_id IN (SELECT id FROM crawls WHERE user_id = (select auth.uid())));

CREATE POLICY "Users can insert own site_structure"
  ON site_structure FOR INSERT
  WITH CHECK (crawl_id IN (SELECT id FROM crawls WHERE user_id = (select auth.uid())));

CREATE POLICY "Users can update own site_structure"
  ON site_structure FOR UPDATE
  USING (crawl_id IN (SELECT id FROM crawls WHERE user_id = (select auth.uid())));

CREATE POLICY "Users can delete own site_structure"
  ON site_structure FOR DELETE
  USING (crawl_id IN (SELECT id FROM crawls WHERE user_id = (select auth.uid())));

CREATE POLICY "Service role full access to site_structure"
  ON site_structure FOR ALL
  USING ((select auth.role()) = 'service_role');

-- ============================================================================
-- PART 10: BATCHES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "Users can view their own batches" ON batches;
DROP POLICY IF EXISTS "Users can insert their own batches" ON batches;
DROP POLICY IF EXISTS "Users can update their own batches" ON batches;
DROP POLICY IF EXISTS "Users can delete their own batches" ON batches;
DROP POLICY IF EXISTS "Users can create batches" ON batches;

CREATE POLICY "Users can view their own batches"
  ON batches FOR SELECT
  USING ((select auth.uid()) = user_id);

CREATE POLICY "Users can insert their own batches"
  ON batches FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "Users can update their own batches"
  ON batches FOR UPDATE
  USING ((select auth.uid()) = user_id)
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "Users can delete their own batches"
  ON batches FOR DELETE
  USING ((select auth.uid()) = user_id);

-- ============================================================================
-- PART 11: BATCH_SITES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "Users can view their own batch_sites" ON batch_sites;
DROP POLICY IF EXISTS "Users can insert their own batch_sites" ON batch_sites;
DROP POLICY IF EXISTS "Users can update their own batch_sites" ON batch_sites;
DROP POLICY IF EXISTS "Users can delete their own batch_sites" ON batch_sites;

CREATE POLICY "Users can view their own batch_sites"
  ON batch_sites FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM batches
      WHERE batches.id = batch_sites.batch_id
      AND batches.user_id = (select auth.uid())
    )
  );

CREATE POLICY "Users can insert their own batch_sites"
  ON batch_sites FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM batches
      WHERE batches.id = batch_sites.batch_id
      AND batches.user_id = (select auth.uid())
    )
  );

CREATE POLICY "Users can update their own batch_sites"
  ON batch_sites FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM batches
      WHERE batches.id = batch_sites.batch_id
      AND batches.user_id = (select auth.uid())
    )
  );

CREATE POLICY "Users can delete their own batch_sites"
  ON batch_sites FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM batches
      WHERE batches.id = batch_sites.batch_id
      AND batches.user_id = (select auth.uid())
    )
  );

-- ============================================================================
-- VERIFICATION: Check that policies were updated
-- ============================================================================

-- List all policies to verify
SELECT
  schemaname,
  tablename,
  policyname,
  cmd,
  qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
