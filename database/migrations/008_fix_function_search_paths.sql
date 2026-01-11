-- Migration: Fix Function Search Paths
-- Version: 008
-- Description: Fix function_search_path_mutable warnings by setting search_path on functions
-- Date: 2026-01-11

-- ============================================================================
-- ISSUE: function_search_path_mutable
-- Functions with mutable search_path can be exploited through search_path manipulation.
-- Fix: Set search_path = '' (empty) which requires all objects to be schema-qualified.
-- ============================================================================

-- Fix handle_new_user function
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, role)
  VALUES (NEW.id, NEW.email, 'admin');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

-- Fix update_updated_at_column function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix test_rls_policies function
CREATE OR REPLACE FUNCTION public.test_rls_policies()
RETURNS TABLE(test_name TEXT, passed BOOLEAN, details TEXT) AS $$
BEGIN
  -- Test 1: Verify RLS is enabled on all tables
  RETURN QUERY
  SELECT
    'RLS Enabled Check'::TEXT,
    BOOL_AND(c.relrowsecurity)::BOOLEAN,
    'All user tables have RLS enabled'::TEXT
  FROM pg_class c
  WHERE c.relname IN ('users', 'crawls', 'pages', 'links', 'images', 'seo_metadata', 'issues', 'summaries', 'site_structure')
  AND c.relnamespace = 'public'::regnamespace;

  -- Test 2: Check if policies exist
  RETURN QUERY
  SELECT
    'Policies Exist Check'::TEXT,
    (COUNT(*) >= 10)::BOOLEAN,
    'Found ' || COUNT(*) || ' policies'::TEXT
  FROM pg_policies
  WHERE schemaname = 'public';

END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

-- ============================================================================
-- NOTE: Other warnings we are NOT addressing in this migration:
--
-- 1. extension_in_public (vector extension)
--    - Moving extensions is complex and could break functionality
--    - Low risk, not worth the potential breakage
--
-- 2. rls_policy_always_true (Service role policies)
--    - These are INTENTIONAL - service role needs full access for backend operations
--    - Example: "Service role full access to crawls" USING (auth.role() = 'service_role')
--    - This always returns true FOR service role users, which is by design
--
-- 3. auth_leaked_password_protection
--    - This is a Supabase Auth dashboard setting, not a SQL configuration
--    - Enable via: Supabase Dashboard > Authentication > Settings > Security
-- ============================================================================
