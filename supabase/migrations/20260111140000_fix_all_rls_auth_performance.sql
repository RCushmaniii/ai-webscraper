-- Migration: Fix ALL RLS Auth Performance (Comprehensive)
-- Version: 010
-- Description: Fix ALL 133+ RLS policies to use (select auth.uid()) instead of auth.uid()
-- Date: 2026-01-11
--
-- This migration drops ALL existing policies and recreates them with optimized subqueries
-- to prevent per-row re-evaluation of auth functions.
--
-- ============================================================================

-- ============================================================================
-- USERS TABLE
-- ============================================================================

DROP POLICY IF EXISTS "users_select_own" ON users;
DROP POLICY IF EXISTS "users_insert_own" ON users;
DROP POLICY IF EXISTS "users_update_own" ON users;
DROP POLICY IF EXISTS "users_delete_own" ON users;
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can insert their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;
DROP POLICY IF EXISTS "Users can delete their own data" ON users;

CREATE POLICY "users_select_own" ON users FOR SELECT
  USING ((select auth.uid()) = id);

CREATE POLICY "users_insert_own" ON users FOR INSERT
  WITH CHECK ((select auth.uid()) = id);

CREATE POLICY "users_update_own" ON users FOR UPDATE
  USING ((select auth.uid()) = id)
  WITH CHECK ((select auth.uid()) = id);

CREATE POLICY "users_delete_own" ON users FOR DELETE
  USING ((select auth.uid()) = id);

-- ============================================================================
-- CRAWLS TABLE
-- ============================================================================

DROP POLICY IF EXISTS "crawls_select_own" ON crawls;
DROP POLICY IF EXISTS "crawls_insert_own" ON crawls;
DROP POLICY IF EXISTS "crawls_update_own" ON crawls;
DROP POLICY IF EXISTS "crawls_delete_own" ON crawls;
DROP POLICY IF EXISTS "Users can view their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can insert their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can create crawls" ON crawls;
DROP POLICY IF EXISTS "Users can update their own crawls" ON crawls;
DROP POLICY IF EXISTS "Users can delete their own crawls" ON crawls;

CREATE POLICY "crawls_select_own" ON crawls FOR SELECT
  USING ((select auth.uid()) = user_id);

CREATE POLICY "crawls_insert_own" ON crawls FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "crawls_update_own" ON crawls FOR UPDATE
  USING ((select auth.uid()) = user_id)
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "crawls_delete_own" ON crawls FOR DELETE
  USING ((select auth.uid()) = user_id);

-- ============================================================================
-- PAGES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "pages_select_own" ON pages;
DROP POLICY IF EXISTS "pages_insert_own" ON pages;
DROP POLICY IF EXISTS "pages_update_own" ON pages;
DROP POLICY IF EXISTS "pages_delete_own" ON pages;
DROP POLICY IF EXISTS "Users can view their own pages" ON pages;
DROP POLICY IF EXISTS "Users can insert pages" ON pages;
DROP POLICY IF EXISTS "Users can update pages" ON pages;
DROP POLICY IF EXISTS "Users can delete pages" ON pages;

CREATE POLICY "pages_select_own" ON pages FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = pages.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "pages_insert_own" ON pages FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = pages.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "pages_update_own" ON pages FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = pages.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "pages_delete_own" ON pages FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = pages.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

-- ============================================================================
-- LINKS TABLE
-- ============================================================================

DROP POLICY IF EXISTS "links_select_own" ON links;
DROP POLICY IF EXISTS "links_insert_own" ON links;
DROP POLICY IF EXISTS "links_update_own" ON links;
DROP POLICY IF EXISTS "links_delete_own" ON links;
DROP POLICY IF EXISTS "Users can view their own links" ON links;
DROP POLICY IF EXISTS "Users can insert links" ON links;
DROP POLICY IF EXISTS "Users can update links" ON links;
DROP POLICY IF EXISTS "Users can delete links" ON links;

CREATE POLICY "links_select_own" ON links FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = links.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "links_insert_own" ON links FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = links.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "links_update_own" ON links FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = links.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "links_delete_own" ON links FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = links.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

-- ============================================================================
-- IMAGES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "images_select_own" ON images;
DROP POLICY IF EXISTS "images_insert_own" ON images;
DROP POLICY IF EXISTS "images_update_own" ON images;
DROP POLICY IF EXISTS "images_delete_own" ON images;
DROP POLICY IF EXISTS "Users can view their own images" ON images;
DROP POLICY IF EXISTS "Users can insert images" ON images;
DROP POLICY IF EXISTS "Users can update images" ON images;
DROP POLICY IF EXISTS "Users can delete images" ON images;

CREATE POLICY "images_select_own" ON images FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = images.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "images_insert_own" ON images FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = images.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "images_update_own" ON images FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = images.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "images_delete_own" ON images FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = images.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

-- ============================================================================
-- SEO_METADATA TABLE
-- ============================================================================

DROP POLICY IF EXISTS "seo_metadata_select_own" ON seo_metadata;
DROP POLICY IF EXISTS "seo_metadata_insert_own" ON seo_metadata;
DROP POLICY IF EXISTS "seo_metadata_update_own" ON seo_metadata;
DROP POLICY IF EXISTS "seo_metadata_delete_own" ON seo_metadata;
DROP POLICY IF EXISTS "Users can view their own seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can insert seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can update seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "Users can delete seo_metadata" ON seo_metadata;

CREATE POLICY "seo_metadata_select_own" ON seo_metadata FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM pages
    INNER JOIN crawls ON crawls.id = pages.crawl_id
    WHERE pages.id = seo_metadata.page_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "seo_metadata_insert_own" ON seo_metadata FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM pages
    INNER JOIN crawls ON crawls.id = pages.crawl_id
    WHERE pages.id = seo_metadata.page_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "seo_metadata_update_own" ON seo_metadata FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM pages
    INNER JOIN crawls ON crawls.id = pages.crawl_id
    WHERE pages.id = seo_metadata.page_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "seo_metadata_delete_own" ON seo_metadata FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM pages
    INNER JOIN crawls ON crawls.id = pages.crawl_id
    WHERE pages.id = seo_metadata.page_id
    AND crawls.user_id = (select auth.uid())
  ));

-- ============================================================================
-- ISSUES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "issues_select_own" ON issues;
DROP POLICY IF EXISTS "issues_insert_own" ON issues;
DROP POLICY IF EXISTS "issues_update_own" ON issues;
DROP POLICY IF EXISTS "issues_delete_own" ON issues;
DROP POLICY IF EXISTS "Users can view their own issues" ON issues;
DROP POLICY IF EXISTS "Users can insert issues" ON issues;
DROP POLICY IF EXISTS "Users can update issues" ON issues;
DROP POLICY IF EXISTS "Users can delete issues" ON issues;

CREATE POLICY "issues_select_own" ON issues FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = issues.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "issues_insert_own" ON issues FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = issues.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "issues_update_own" ON issues FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = issues.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "issues_delete_own" ON issues FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = issues.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

-- ============================================================================
-- SUMMARIES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "summaries_select_own" ON summaries;
DROP POLICY IF EXISTS "summaries_insert_own" ON summaries;
DROP POLICY IF EXISTS "summaries_update_own" ON summaries;
DROP POLICY IF EXISTS "summaries_delete_own" ON summaries;
DROP POLICY IF EXISTS "Users can view their own summaries" ON summaries;
DROP POLICY IF EXISTS "Users can insert summaries" ON summaries;
DROP POLICY IF EXISTS "Users can update summaries" ON summaries;
DROP POLICY IF EXISTS "Users can delete summaries" ON summaries;

CREATE POLICY "summaries_select_own" ON summaries FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = summaries.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "summaries_insert_own" ON summaries FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = summaries.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "summaries_update_own" ON summaries FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = summaries.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "summaries_delete_own" ON summaries FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = summaries.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

-- ============================================================================
-- BATCHES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "batches_select_own" ON batches;
DROP POLICY IF EXISTS "batches_insert_own" ON batches;
DROP POLICY IF EXISTS "batches_update_own" ON batches;
DROP POLICY IF EXISTS "batches_delete_own" ON batches;
DROP POLICY IF EXISTS "Users can view their own batches" ON batches;
DROP POLICY IF EXISTS "Users can insert their own batches" ON batches;
DROP POLICY IF EXISTS "Users can create batches" ON batches;
DROP POLICY IF EXISTS "Users can update their own batches" ON batches;
DROP POLICY IF EXISTS "Users can delete their own batches" ON batches;

CREATE POLICY "batches_select_own" ON batches FOR SELECT
  USING ((select auth.uid()) = user_id);

CREATE POLICY "batches_insert_own" ON batches FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "batches_update_own" ON batches FOR UPDATE
  USING ((select auth.uid()) = user_id)
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "batches_delete_own" ON batches FOR DELETE
  USING ((select auth.uid()) = user_id);

-- ============================================================================
-- BATCH_SITES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "batch_sites_select_own" ON batch_sites;
DROP POLICY IF EXISTS "batch_sites_insert_own" ON batch_sites;
DROP POLICY IF EXISTS "batch_sites_update_own" ON batch_sites;
DROP POLICY IF EXISTS "batch_sites_delete_own" ON batch_sites;
DROP POLICY IF EXISTS "Users can view their own batch_sites" ON batch_sites;
DROP POLICY IF EXISTS "Users can insert batch_sites" ON batch_sites;
DROP POLICY IF EXISTS "Users can update batch_sites" ON batch_sites;
DROP POLICY IF EXISTS "Users can delete batch_sites" ON batch_sites;

CREATE POLICY "batch_sites_select_own" ON batch_sites FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM batches
    WHERE batches.id = batch_sites.batch_id
    AND batches.user_id = (select auth.uid())
  ));

CREATE POLICY "batch_sites_insert_own" ON batch_sites FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM batches
    WHERE batches.id = batch_sites.batch_id
    AND batches.user_id = (select auth.uid())
  ));

CREATE POLICY "batch_sites_update_own" ON batch_sites FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM batches
    WHERE batches.id = batch_sites.batch_id
    AND batches.user_id = (select auth.uid())
  ));

CREATE POLICY "batch_sites_delete_own" ON batch_sites FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM batches
    WHERE batches.id = batch_sites.batch_id
    AND batches.user_id = (select auth.uid())
  ));

-- ============================================================================
-- AUDIT_LOG TABLE
-- ============================================================================

DROP POLICY IF EXISTS "audit_log_select_own" ON audit_log;
DROP POLICY IF EXISTS "audit_log_insert_own" ON audit_log;
DROP POLICY IF EXISTS "Users can view their own audit_log" ON audit_log;
DROP POLICY IF EXISTS "Users can insert their own audit_log" ON audit_log;

CREATE POLICY "audit_log_select_own" ON audit_log FOR SELECT
  USING ((select auth.uid()) = user_id);

CREATE POLICY "audit_log_insert_own" ON audit_log FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

-- ============================================================================
-- GOOGLE_PLACES TABLE
-- ============================================================================

DROP POLICY IF EXISTS "google_places_select_own" ON google_places;
DROP POLICY IF EXISTS "google_places_insert_own" ON google_places;
DROP POLICY IF EXISTS "google_places_update_own" ON google_places;
DROP POLICY IF EXISTS "google_places_delete_own" ON google_places;
DROP POLICY IF EXISTS "Users can view their own google_places" ON google_places;
DROP POLICY IF EXISTS "Users can insert their own google_places" ON google_places;
DROP POLICY IF EXISTS "Users can update their own google_places" ON google_places;
DROP POLICY IF EXISTS "Users can delete their own google_places" ON google_places;

CREATE POLICY "google_places_select_own" ON google_places FOR SELECT
  USING ((select auth.uid()) = user_id);

CREATE POLICY "google_places_insert_own" ON google_places FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "google_places_update_own" ON google_places FOR UPDATE
  USING ((select auth.uid()) = user_id)
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "google_places_delete_own" ON google_places FOR DELETE
  USING ((select auth.uid()) = user_id);

-- ============================================================================
-- SITE_STRUCTURE TABLE
-- ============================================================================

DROP POLICY IF EXISTS "site_structure_select_own" ON site_structure;
DROP POLICY IF EXISTS "site_structure_insert_own" ON site_structure;
DROP POLICY IF EXISTS "site_structure_update_own" ON site_structure;
DROP POLICY IF EXISTS "site_structure_delete_own" ON site_structure;
DROP POLICY IF EXISTS "Users can view own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Users can insert own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Users can update own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Users can delete own site_structure" ON site_structure;
DROP POLICY IF EXISTS "Service role full access to site_structure" ON site_structure;

CREATE POLICY "site_structure_select_own" ON site_structure FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = site_structure.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "site_structure_insert_own" ON site_structure FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = site_structure.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "site_structure_update_own" ON site_structure FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = site_structure.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

CREATE POLICY "site_structure_delete_own" ON site_structure FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM crawls
    WHERE crawls.id = site_structure.crawl_id
    AND crawls.user_id = (select auth.uid())
  ));

-- Service role bypass for backend operations
CREATE POLICY "site_structure_service_role" ON site_structure FOR ALL
  USING ((select auth.role()) = 'service_role');

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
