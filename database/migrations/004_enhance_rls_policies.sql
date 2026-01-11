-- ============================================================================
-- RLS Enhancement Migration - Production-Ready Security Policies
-- ============================================================================
--
-- Following Best Practices:
-- ✅ Use BOTH "USING" and "WITH CHECK" for write operations
-- ✅ Test: Logged-in user, No auth, Insert attack
-- ✅ Enable RLS on all user data tables
-- ✅ Never trust frontend checks
-- ✅ Service role bypasses RLS (backend only)
--
-- ============================================================================

-- ============================================================================
-- PART 1: Ensure RLS is ENABLED on all user data tables
-- ============================================================================

ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS crawls ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS links ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS images ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS seo_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS summaries ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- PART 2: DROP existing policies (clean slate)
-- ============================================================================

-- Users table
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "users_select_own" ON users;
DROP POLICY IF EXISTS "Only admins can insert" ON users;
DROP POLICY IF EXISTS "users_insert_own" ON users;
DROP POLICY IF EXISTS "Only admins can update" ON users;
DROP POLICY IF EXISTS "users_update_own" ON users;
DROP POLICY IF EXISTS "users_delete_own" ON users;

-- Crawls table
DROP POLICY IF EXISTS "Users can view their own crawls" ON crawls;
DROP POLICY IF EXISTS "crawls_select_own" ON crawls;
DROP POLICY IF EXISTS "Users can insert their own crawls" ON crawls;
DROP POLICY IF EXISTS "crawls_insert_own" ON crawls;
DROP POLICY IF EXISTS "Users can update their own crawls" ON crawls;
DROP POLICY IF EXISTS "crawls_update_own" ON crawls;
DROP POLICY IF EXISTS "Users can delete their own crawls" ON crawls;
DROP POLICY IF EXISTS "crawls_delete_own" ON crawls;

-- Pages table
DROP POLICY IF EXISTS "Users can view their own pages" ON pages;
DROP POLICY IF EXISTS "pages_select_own" ON pages;

-- Links table
DROP POLICY IF EXISTS "Users can view their own links" ON links;
DROP POLICY IF EXISTS "links_select_own" ON links;

-- Images table
DROP POLICY IF EXISTS "Users can view their own images" ON images;
DROP POLICY IF EXISTS "images_select_own" ON images;

-- SEO Metadata table
DROP POLICY IF EXISTS "Users can view their own seo_metadata" ON seo_metadata;
DROP POLICY IF EXISTS "seo_metadata_select_own" ON seo_metadata;

-- Issues table
DROP POLICY IF EXISTS "Users can view their own issues" ON issues;
DROP POLICY IF EXISTS "issues_select_own" ON issues;

-- Summaries table
DROP POLICY IF EXISTS "Users can view their own summaries" ON summaries;
DROP POLICY IF EXISTS "summaries_select_own" ON summaries;

-- ============================================================================
-- PART 3: USERS TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view their own profile
CREATE POLICY "users_select_own"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- INSERT: Only authenticated users can create their own record
-- (Usually handled by Supabase Auth triggers, but good to have as safeguard)
CREATE POLICY "users_insert_own"
  ON users FOR INSERT
  WITH CHECK (auth.uid() = id);

-- UPDATE: Users can update their own profile
-- CRITICAL: Both USING and WITH CHECK prevent ownership transfer
CREATE POLICY "users_update_own"
  ON users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- DELETE: Users can delete their own account (GDPR compliance)
CREATE POLICY "users_delete_own"
  ON users FOR DELETE
  USING (auth.uid() = id);

-- ============================================================================
-- PART 4: CRAWLS TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view their own crawls
CREATE POLICY "crawls_select_own"
  ON crawls FOR SELECT
  USING (auth.uid() = user_id);

-- INSERT: Users can create crawls for themselves
-- CRITICAL: WITH CHECK prevents user from setting user_id to someone else
CREATE POLICY "crawls_insert_own"
  ON crawls FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- UPDATE: Users can update their own crawls
-- CRITICAL: Both USING and WITH CHECK prevent ownership transfer
CREATE POLICY "crawls_update_own"
  ON crawls FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- DELETE: Users can delete their own crawls
CREATE POLICY "crawls_delete_own"
  ON crawls FOR DELETE
  USING (auth.uid() = user_id);

-- ============================================================================
-- PART 5: PAGES TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view pages from their own crawls
CREATE POLICY "pages_select_own"
  ON pages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Note: INSERT/UPDATE/DELETE for pages should only happen via service role (crawler)
-- Users should NOT directly modify pages

-- ============================================================================
-- PART 6: LINKS TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view links from their own crawls
CREATE POLICY "links_select_own"
  ON links FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Note: INSERT/UPDATE/DELETE via service role only (crawler inserts links)

-- ============================================================================
-- PART 7: IMAGES TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view images from their own crawls
CREATE POLICY "images_select_own"
  ON images FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = images.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Note: INSERT/UPDATE/DELETE via service role only (crawler inserts images)

-- ============================================================================
-- PART 8: SEO_METADATA TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view SEO metadata from their own crawls
CREATE POLICY "seo_metadata_select_own"
  ON seo_metadata FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM pages
      INNER JOIN crawls ON crawls.id = pages.crawl_id
      WHERE pages.id = seo_metadata.page_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Note: INSERT/UPDATE/DELETE via service role only (crawler inserts metadata)

-- ============================================================================
-- PART 9: ISSUES TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view issues from their own crawls
CREATE POLICY "issues_select_own"
  ON issues FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = issues.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Note: INSERT/UPDATE/DELETE via service role only (issue detector inserts issues)

-- ============================================================================
-- PART 10: SUMMARIES TABLE - Enhanced Policies
-- ============================================================================

-- SELECT: Users can view summaries from their own crawls
CREATE POLICY "summaries_select_own"
  ON summaries FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = summaries.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Note: INSERT/UPDATE/DELETE via service role only (summarizer inserts summaries)

-- ============================================================================
-- PART 11: ADD HELPFUL COMMENTS
-- ============================================================================

COMMENT ON POLICY "crawls_select_own" ON crawls IS
  'Users can only view their own crawls. USING checks user_id = auth.uid()';

COMMENT ON POLICY "crawls_insert_own" ON crawls IS
  'Users can only create crawls for themselves. WITH CHECK prevents setting user_id to another user.';

COMMENT ON POLICY "crawls_update_own" ON crawls IS
  'Users can only update their own crawls. Both USING and WITH CHECK prevent ownership transfer.';

COMMENT ON POLICY "pages_select_own" ON pages IS
  'Users can only view pages from their own crawls. Uses EXISTS subquery to check crawl ownership.';

-- ============================================================================
-- PART 12: VERIFICATION FUNCTION
-- ============================================================================

-- Function to test RLS policies
CREATE OR REPLACE FUNCTION test_rls_policies()
RETURNS TABLE(test_name TEXT, passed BOOLEAN, details TEXT) AS $$
BEGIN
  -- Test 1: Verify RLS is enabled on all tables
  RETURN QUERY
  SELECT
    'RLS Enabled Check'::TEXT,
    BOOL_AND(c.relrowsecurity)::BOOLEAN,
    'All user tables have RLS enabled'::TEXT
  FROM pg_class c
  WHERE c.relname IN ('users', 'crawls', 'pages', 'links', 'images', 'seo_metadata', 'issues', 'summaries')
  AND c.relnamespace = 'public'::regnamespace;

  -- Test 2: Check if policies exist
  RETURN QUERY
  SELECT
    'Policies Exist Check'::TEXT,
    COUNT(*) >= 10::BOOLEAN,
    'Found ' || COUNT(*) || ' policies'::TEXT
  FROM pg_policies
  WHERE schemaname = 'public';

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Run verification
SELECT * FROM test_rls_policies();

-- ============================================================================
-- PART 13: TESTING NOTES (for manual verification)
-- ============================================================================

-- To test manually in Supabase SQL Editor:

-- Test 1: Logged-in user can see own data
-- SELECT auth.uid(); -- Should return your user ID
-- SELECT * FROM crawls WHERE user_id = auth.uid(); -- Should return your crawls
-- SELECT * FROM crawls WHERE user_id != auth.uid(); -- Should return 0 rows

-- Test 2: Insert attack should fail
-- INSERT INTO crawls (user_id, url, name, status, max_depth, max_pages, respect_robots_txt, follow_external_links, js_rendering, rate_limit, created_at, updated_at)
-- VALUES ('some-other-user-id', 'https://example.com', 'Test', 'pending', 2, 100, true, false, false, 2, now(), now());
-- Should fail with: new row violates row-level security policy

-- Test 3: Service role bypasses RLS (backend only)
-- This is automatic - service role key bypasses all RLS policies

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
