-- Add html_storage_path column to pages table
-- The code writes html_storage_path but the DB only has html_snapshot_path
ALTER TABLE pages ADD COLUMN IF NOT EXISTS html_storage_path TEXT;
