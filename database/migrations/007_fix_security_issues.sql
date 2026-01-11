-- Migration: Fix Security Issues (Supabase Linter Errors)
-- Version: 007
-- Description: Fix SECURITY DEFINER views and enable RLS on site_structure
-- Date: 2026-01-11

-- ============================================================================
-- ISSUE 1 & 2: Fix SECURITY DEFINER views
-- ============================================================================

-- Drop the views
DROP VIEW IF EXISTS public.page_analysis_details CASCADE;
DROP VIEW IF EXISTS public.crawl_analysis_summary CASCADE;

-- Recreate page_analysis_details view WITHOUT SECURITY DEFINER
CREATE OR REPLACE VIEW public.page_analysis_details AS
SELECT
    p.id AS page_id,
    p.crawl_id,
    p.url,
    p.title,
    p.status_code,
    p.response_time,
    p.content_type,
    p.content_length,
    p.h1_tags,
    p.h2_tags,
    p.internal_links,
    p.external_links,
    p.images AS image_count,
    p.seo_score,
    p.is_primary,
    p.nav_score,
    p.created_at AS page_created_at,
    sm.meta_description,
    sm.title_length,
    sm.meta_description_length,
    sm.canonical,
    sm.robots_meta,
    sm.og_tags,
    sm.twitter_tags
FROM pages p
LEFT JOIN seo_metadata sm ON p.id = sm.page_id;

COMMENT ON VIEW public.page_analysis_details IS 'Combined view of pages with SEO metadata. Uses SECURITY INVOKER to respect RLS.';

-- Recreate crawl_analysis_summary view WITHOUT SECURITY DEFINER
CREATE OR REPLACE VIEW public.crawl_analysis_summary AS
SELECT
    c.id AS crawl_id,
    c.url AS start_url,
    c.name AS crawl_name,
    c.status,
    c.created_at,
    c.completed_at,
    c.user_id,
    COUNT(DISTINCT p.id) AS total_pages,
    COUNT(DISTINCT CASE WHEN p.status_code >= 200 AND p.status_code < 300 THEN p.id END) AS success_pages,
    COUNT(DISTINCT CASE WHEN p.status_code >= 400 THEN p.id END) AS error_pages,
    COUNT(DISTINCT CASE WHEN p.is_primary = true THEN p.id END) AS main_pages,
    COUNT(DISTINCT l.id) AS total_links,
    COUNT(DISTINCT CASE WHEN l.is_broken = true THEN l.id END) AS broken_links,
    COUNT(DISTINCT i.id) AS total_images,
    COUNT(DISTINCT CASE WHEN i.has_alt = false THEN i.id END) AS images_missing_alt,
    COUNT(DISTINCT iss.id) AS total_issues,
    COUNT(DISTINCT CASE WHEN iss.severity = 'critical' THEN iss.id END) AS critical_issues,
    COUNT(DISTINCT CASE WHEN iss.severity = 'high' THEN iss.id END) AS high_issues,
    AVG(p.response_time)::integer AS avg_response_time,
    AVG(p.seo_score)::integer AS avg_seo_score
FROM crawls c
LEFT JOIN pages p ON c.id = p.crawl_id
LEFT JOIN links l ON c.id = l.crawl_id
LEFT JOIN images i ON c.id = i.crawl_id
LEFT JOIN issues iss ON c.id = iss.crawl_id
GROUP BY c.id, c.url, c.name, c.status, c.created_at, c.completed_at, c.user_id;

COMMENT ON VIEW public.crawl_analysis_summary IS 'Aggregate statistics for crawls. Uses SECURITY INVOKER to respect RLS.';

-- ============================================================================
-- ISSUE 3: Enable RLS on site_structure table
-- ============================================================================

ALTER TABLE public.site_structure ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any (to avoid conflicts)
DROP POLICY IF EXISTS "Users can view own site_structure" ON public.site_structure;
DROP POLICY IF EXISTS "Users can insert own site_structure" ON public.site_structure;
DROP POLICY IF EXISTS "Users can update own site_structure" ON public.site_structure;
DROP POLICY IF EXISTS "Users can delete own site_structure" ON public.site_structure;
DROP POLICY IF EXISTS "Service role full access to site_structure" ON public.site_structure;

-- Create RLS policies
CREATE POLICY "Users can view own site_structure"
    ON public.site_structure FOR SELECT
    USING (crawl_id IN (SELECT id FROM crawls WHERE user_id = auth.uid()));

CREATE POLICY "Users can insert own site_structure"
    ON public.site_structure FOR INSERT
    WITH CHECK (crawl_id IN (SELECT id FROM crawls WHERE user_id = auth.uid()));

CREATE POLICY "Users can update own site_structure"
    ON public.site_structure FOR UPDATE
    USING (crawl_id IN (SELECT id FROM crawls WHERE user_id = auth.uid()));

CREATE POLICY "Users can delete own site_structure"
    ON public.site_structure FOR DELETE
    USING (crawl_id IN (SELECT id FROM crawls WHERE user_id = auth.uid()));

CREATE POLICY "Service role full access to site_structure"
    ON public.site_structure FOR ALL
    USING (auth.role() = 'service_role');

COMMENT ON TABLE public.site_structure IS 'Site structure analysis. RLS enabled.';
