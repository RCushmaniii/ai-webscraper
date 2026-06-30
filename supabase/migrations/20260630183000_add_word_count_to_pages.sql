-- Add the missing word_count column to the pages table.
--
-- Why: PR #82 (2026-06-29) added code that WRITES word_count on every page save
-- (crawler.py:_save_page_to_db) and READS it during report generation
-- (analysis.py), but no migration ever created the column. The base schema in
-- database/migrations/PRODUCTION_READY_MIGRATION.sql defines it, but that manual
-- file was never part of the Supabase CLI migration set applied to this project,
-- so production's pages table never had it.
--
-- Impact this fixes: every _save_page_to_db insert was throwing
-- "column pages.word_count does not exist" (Postgres 42703), so fresh crawls
-- saved ZERO pages while the worker still reported "completed". Fresh AI report
-- generation was also broken for the same reason (its SELECT names word_count).
--
-- word_count = the main-content word count of the page (NULL on rows created
-- before this column existed; those need a re-crawl to populate).

ALTER TABLE pages
ADD COLUMN IF NOT EXISTS word_count INTEGER;

COMMENT ON COLUMN pages.word_count IS
  'Main-content word count for the page. Written by the crawler; used for thin-content detection and report metrics. NULL for rows crawled before 2026-06-30.';
