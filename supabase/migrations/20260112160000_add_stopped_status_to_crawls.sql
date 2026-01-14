-- Migration: Add 'stopped' and 'cancelled' to crawls status CHECK constraint
-- Version: 016
-- Description: Allow crawls to be stopped/cancelled
-- Date: 2026-01-12

-- Drop the existing constraint and add a new one with additional statuses
ALTER TABLE crawls DROP CONSTRAINT IF EXISTS crawls_status_check;

ALTER TABLE crawls ADD CONSTRAINT crawls_status_check
  CHECK (status IN ('pending', 'queued', 'running', 'in_progress', 'completed', 'failed', 'stopped', 'cancelled'));

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
