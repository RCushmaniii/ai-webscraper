-- Migration: Drop "System can manage tasks" policy
-- Version: 013
-- Description: Remove legacy policy causing multiple permissive warnings
-- Date: 2026-01-11

DROP POLICY IF EXISTS "System can manage tasks" ON tasks;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
