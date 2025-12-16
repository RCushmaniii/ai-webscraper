-- This migration renames the 'start_url' column to 'url' in the 'crawls' table.
-- Run this script in your Supabase SQL Editor to apply the change.

ALTER TABLE crawls RENAME COLUMN start_url TO url;
