-- Migration: FINAL RLS Cleanup
-- Version: 012
-- Description:
--   1. Remove ALL service_role policies (causing "multiple permissive" warnings)
--   2. Drop ALL legacy policy names
--   3. Add missing tables: tasks, page_analysis, crawl_analysis, page_embeddings, llm_usage, image_analysis
--   4. Ensure all policies use (select auth.uid())
-- Date: 2026-01-11
--
-- NOTE: Service role key BYPASSES RLS entirely, so service_role policies are unnecessary!
--
-- ============================================================================

-- ============================================================================
-- STEP 1: DROP ALL SERVICE_ROLE POLICIES (causing multiple permissive warnings)
-- ============================================================================

DROP POLICY IF EXISTS "pages_service_role" ON pages;
DROP POLICY IF EXISTS "links_service_role" ON links;
DROP POLICY IF EXISTS "images_service_role" ON images;
DROP POLICY IF EXISTS "seo_metadata_service_role" ON seo_metadata;
DROP POLICY IF EXISTS "issues_service_role" ON issues;
DROP POLICY IF EXISTS "summaries_service_role" ON summaries;
DROP POLICY IF EXISTS "site_structure_service_role" ON site_structure;

-- Also drop "System can X" policies (these also cause multiple permissive)
DROP POLICY IF EXISTS "System can insert pages" ON pages;
DROP POLICY IF EXISTS "System can update pages" ON pages;
DROP POLICY IF EXISTS "System can select pages" ON pages;
DROP POLICY IF EXISTS "System can delete pages" ON pages;

-- ============================================================================
-- STEP 2: DROP LEGACY POLICY NAMES I MISSED
-- ============================================================================

DROP POLICY IF EXISTS "pages_select_via_crawl" ON pages;

-- ============================================================================
-- STEP 3: TASKS TABLE - Fix and ensure optimized
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'tasks') THEN
    -- Drop all existing policies
    EXECUTE 'DROP POLICY IF EXISTS "Users can view own tasks" ON tasks';
    EXECUTE 'DROP POLICY IF EXISTS "Users can insert own tasks" ON tasks';
    EXECUTE 'DROP POLICY IF EXISTS "Users can update own tasks" ON tasks';
    EXECUTE 'DROP POLICY IF EXISTS "Users can delete own tasks" ON tasks';
    EXECUTE 'DROP POLICY IF EXISTS "tasks_select_own" ON tasks';
    EXECUTE 'DROP POLICY IF EXISTS "tasks_insert_own" ON tasks';
    EXECUTE 'DROP POLICY IF EXISTS "tasks_update_own" ON tasks';
    EXECUTE 'DROP POLICY IF EXISTS "tasks_delete_own" ON tasks';

    -- Check if tasks has user_id column or crawl_id column
    IF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tasks' AND column_name = 'user_id') THEN
      EXECUTE 'CREATE POLICY "tasks_select_own" ON tasks FOR SELECT USING ((select auth.uid()) = user_id)';
      EXECUTE 'CREATE POLICY "tasks_insert_own" ON tasks FOR INSERT WITH CHECK ((select auth.uid()) = user_id)';
      EXECUTE 'CREATE POLICY "tasks_update_own" ON tasks FOR UPDATE USING ((select auth.uid()) = user_id) WITH CHECK ((select auth.uid()) = user_id)';
      EXECUTE 'CREATE POLICY "tasks_delete_own" ON tasks FOR DELETE USING ((select auth.uid()) = user_id)';
    ELSIF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tasks' AND column_name = 'crawl_id') THEN
      EXECUTE 'CREATE POLICY "tasks_select_own" ON tasks FOR SELECT USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = tasks.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "tasks_insert_own" ON tasks FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = tasks.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "tasks_update_own" ON tasks FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = tasks.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "tasks_delete_own" ON tasks FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = tasks.crawl_id AND crawls.user_id = (select auth.uid())))';
    END IF;
  END IF;
END $$;

-- ============================================================================
-- STEP 4: PAGE_ANALYSIS TABLE
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'page_analysis') THEN
    EXECUTE 'DROP POLICY IF EXISTS "Users can view own page analyses" ON page_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can insert own page analyses" ON page_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can update own page analyses" ON page_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can delete own page analyses" ON page_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "page_analysis_select_own" ON page_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "page_analysis_insert_own" ON page_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "page_analysis_update_own" ON page_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "page_analysis_delete_own" ON page_analysis';

    -- Check structure
    IF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'page_analysis' AND column_name = 'crawl_id') THEN
      EXECUTE 'CREATE POLICY "page_analysis_select_own" ON page_analysis FOR SELECT USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = page_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_analysis_insert_own" ON page_analysis FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = page_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_analysis_update_own" ON page_analysis FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = page_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_analysis_delete_own" ON page_analysis FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = page_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
    ELSIF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'page_analysis' AND column_name = 'page_id') THEN
      EXECUTE 'CREATE POLICY "page_analysis_select_own" ON page_analysis FOR SELECT USING (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_analysis.page_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_analysis_insert_own" ON page_analysis FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_analysis.page_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_analysis_update_own" ON page_analysis FOR UPDATE USING (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_analysis.page_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_analysis_delete_own" ON page_analysis FOR DELETE USING (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_analysis.page_id AND crawls.user_id = (select auth.uid())))';
    END IF;
  END IF;
END $$;

-- ============================================================================
-- STEP 5: CRAWL_ANALYSIS TABLE
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'crawl_analysis') THEN
    EXECUTE 'DROP POLICY IF EXISTS "Users can view own crawl analyses" ON crawl_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can insert own crawl analyses" ON crawl_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can update own crawl analyses" ON crawl_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can delete own crawl analyses" ON crawl_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "crawl_analysis_select_own" ON crawl_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "crawl_analysis_insert_own" ON crawl_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "crawl_analysis_update_own" ON crawl_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "crawl_analysis_delete_own" ON crawl_analysis';

    EXECUTE 'CREATE POLICY "crawl_analysis_select_own" ON crawl_analysis FOR SELECT USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = crawl_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
    EXECUTE 'CREATE POLICY "crawl_analysis_insert_own" ON crawl_analysis FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = crawl_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
    EXECUTE 'CREATE POLICY "crawl_analysis_update_own" ON crawl_analysis FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = crawl_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
    EXECUTE 'CREATE POLICY "crawl_analysis_delete_own" ON crawl_analysis FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = crawl_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
  END IF;
END $$;

-- ============================================================================
-- STEP 6: PAGE_EMBEDDINGS TABLE
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'page_embeddings') THEN
    EXECUTE 'DROP POLICY IF EXISTS "Users can view own embeddings" ON page_embeddings';
    EXECUTE 'DROP POLICY IF EXISTS "Users can insert own embeddings" ON page_embeddings';
    EXECUTE 'DROP POLICY IF EXISTS "Users can update own embeddings" ON page_embeddings';
    EXECUTE 'DROP POLICY IF EXISTS "Users can delete own embeddings" ON page_embeddings';
    EXECUTE 'DROP POLICY IF EXISTS "page_embeddings_select_own" ON page_embeddings';
    EXECUTE 'DROP POLICY IF EXISTS "page_embeddings_insert_own" ON page_embeddings';
    EXECUTE 'DROP POLICY IF EXISTS "page_embeddings_update_own" ON page_embeddings';
    EXECUTE 'DROP POLICY IF EXISTS "page_embeddings_delete_own" ON page_embeddings';

    IF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'page_embeddings' AND column_name = 'page_id') THEN
      EXECUTE 'CREATE POLICY "page_embeddings_select_own" ON page_embeddings FOR SELECT USING (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_embeddings.page_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_embeddings_insert_own" ON page_embeddings FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_embeddings.page_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_embeddings_update_own" ON page_embeddings FOR UPDATE USING (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_embeddings.page_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "page_embeddings_delete_own" ON page_embeddings FOR DELETE USING (EXISTS (SELECT 1 FROM pages INNER JOIN crawls ON crawls.id = pages.crawl_id WHERE pages.id = page_embeddings.page_id AND crawls.user_id = (select auth.uid())))';
    END IF;
  END IF;
END $$;

-- ============================================================================
-- STEP 7: LLM_USAGE TABLE
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'llm_usage') THEN
    EXECUTE 'DROP POLICY IF EXISTS "Users can view own usage" ON llm_usage';
    EXECUTE 'DROP POLICY IF EXISTS "Users can insert own usage" ON llm_usage';
    EXECUTE 'DROP POLICY IF EXISTS "Users can update own usage" ON llm_usage';
    EXECUTE 'DROP POLICY IF EXISTS "Users can delete own usage" ON llm_usage';
    EXECUTE 'DROP POLICY IF EXISTS "llm_usage_select_own" ON llm_usage';
    EXECUTE 'DROP POLICY IF EXISTS "llm_usage_insert_own" ON llm_usage';
    EXECUTE 'DROP POLICY IF EXISTS "llm_usage_update_own" ON llm_usage';
    EXECUTE 'DROP POLICY IF EXISTS "llm_usage_delete_own" ON llm_usage';

    IF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'llm_usage' AND column_name = 'user_id') THEN
      EXECUTE 'CREATE POLICY "llm_usage_select_own" ON llm_usage FOR SELECT USING ((select auth.uid()) = user_id)';
      EXECUTE 'CREATE POLICY "llm_usage_insert_own" ON llm_usage FOR INSERT WITH CHECK ((select auth.uid()) = user_id)';
      EXECUTE 'CREATE POLICY "llm_usage_update_own" ON llm_usage FOR UPDATE USING ((select auth.uid()) = user_id) WITH CHECK ((select auth.uid()) = user_id)';
      EXECUTE 'CREATE POLICY "llm_usage_delete_own" ON llm_usage FOR DELETE USING ((select auth.uid()) = user_id)';
    END IF;
  END IF;
END $$;

-- ============================================================================
-- STEP 8: IMAGE_ANALYSIS TABLE
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'image_analysis') THEN
    EXECUTE 'DROP POLICY IF EXISTS "Users can view own image analyses" ON image_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can insert image analyses for own crawls" ON image_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can update own image analyses" ON image_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "Users can delete own image analyses" ON image_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "image_analysis_select_own" ON image_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "image_analysis_insert_own" ON image_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "image_analysis_update_own" ON image_analysis';
    EXECUTE 'DROP POLICY IF EXISTS "image_analysis_delete_own" ON image_analysis';

    IF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'image_analysis' AND column_name = 'crawl_id') THEN
      EXECUTE 'CREATE POLICY "image_analysis_select_own" ON image_analysis FOR SELECT USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = image_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "image_analysis_insert_own" ON image_analysis FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = image_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "image_analysis_update_own" ON image_analysis FOR UPDATE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = image_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "image_analysis_delete_own" ON image_analysis FOR DELETE USING (EXISTS (SELECT 1 FROM crawls WHERE crawls.id = image_analysis.crawl_id AND crawls.user_id = (select auth.uid())))';
    ELSIF EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'image_analysis' AND column_name = 'image_id') THEN
      EXECUTE 'CREATE POLICY "image_analysis_select_own" ON image_analysis FOR SELECT USING (EXISTS (SELECT 1 FROM images INNER JOIN crawls ON crawls.id = images.crawl_id WHERE images.id = image_analysis.image_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "image_analysis_insert_own" ON image_analysis FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM images INNER JOIN crawls ON crawls.id = images.crawl_id WHERE images.id = image_analysis.image_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "image_analysis_update_own" ON image_analysis FOR UPDATE USING (EXISTS (SELECT 1 FROM images INNER JOIN crawls ON crawls.id = images.crawl_id WHERE images.id = image_analysis.image_id AND crawls.user_id = (select auth.uid())))';
      EXECUTE 'CREATE POLICY "image_analysis_delete_own" ON image_analysis FOR DELETE USING (EXISTS (SELECT 1 FROM images INNER JOIN crawls ON crawls.id = images.crawl_id WHERE images.id = image_analysis.image_id AND crawls.user_id = (select auth.uid())))';
    END IF;
  END IF;
END $$;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
