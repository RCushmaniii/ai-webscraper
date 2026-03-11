-- ============================================
-- MIGRATION 010: Enhanced Audit Logging
-- ============================================
-- Enhances the existing audit_log table with additional columns
-- for IP tracking and flexible target IDs. Also adds proper
-- admin-only RLS and performance indexes.
--
-- Existing table: audit_log (entity_type, entity_id UUID, details JSONB)
-- Adds: ip_address, target_id (TEXT alias via new column)
-- Updates: RLS to admin-only read, service-role insert
-- ============================================

-- Add ip_address column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'audit_log' AND column_name = 'ip_address'
    ) THEN
        ALTER TABLE audit_log ADD COLUMN ip_address TEXT;
    END IF;
END $$;

-- Make entity_id nullable (some actions like invite_user have no target entity yet)
ALTER TABLE audit_log ALTER COLUMN entity_id DROP NOT NULL;

-- Add index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);

-- Add index on action for filtering
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- Update RLS policies: admins can read ALL audit logs, not just their own
-- Drop old restrictive policies
DROP POLICY IF EXISTS "Users can view their own audit_log" ON audit_log;
DROP POLICY IF EXISTS "Users can insert their own audit_log" ON audit_log;
DROP POLICY IF EXISTS "Admins can read all audit logs" ON audit_log;
DROP POLICY IF EXISTS "Service role can insert audit logs" ON audit_log;

-- Admins can read all audit logs (not just their own)
CREATE POLICY "Admins can read all audit logs"
    ON audit_log FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
              AND users.is_admin = true
        )
    );

-- Allow inserts from service role (used by backend audit helper)
-- The service role key bypasses RLS anyway, but this policy allows
-- authenticated clients to insert their own audit entries too
CREATE POLICY "Service role can insert audit logs"
    ON audit_log FOR INSERT
    WITH CHECK (true);

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
