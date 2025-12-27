-- Fix the status check constraint to allow all valid status values
-- Drop the old constraint
ALTER TABLE crawls DROP CONSTRAINT IF EXISTS crawls_status_check;

-- Add new constraint with all valid status values
ALTER TABLE crawls ADD CONSTRAINT crawls_status_check 
  CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled'));
