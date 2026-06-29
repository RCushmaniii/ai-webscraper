-- ============================================
-- Enhanced Audit Logging (ip_address + admin RLS)
-- ============================================
-- Ports database/migrations/010_audit_logs.sql into the Supabase CLI
-- migration set. The original 010 was never applied via `supabase db push`,
-- so production audit_log lacks the ip_address column — every crawl logs a
-- "Could not find the 'ip_address' column" error to Sentry (audit writes are
-- non-fatal, so crawls still succeed). Idempotent.
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

-- Indexes for time-based and action filtering
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- RLS: admins read all audit logs; service-role / authenticated inserts allowed
DROP POLICY IF EXISTS "Users can view their own audit_log" ON audit_log;
DROP POLICY IF EXISTS "Users can insert their own audit_log" ON audit_log;
DROP POLICY IF EXISTS "Admins can read all audit logs" ON audit_log;
DROP POLICY IF EXISTS "Service role can insert audit logs" ON audit_log;

CREATE POLICY "Admins can read all audit logs"
    ON audit_log FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
              AND users.is_admin = true
        )
    );

CREATE POLICY "Service role can insert audit logs"
    ON audit_log FOR INSERT
    WITH CHECK (true);
