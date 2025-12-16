-- Add missing columns to crawls table
ALTER TABLE crawls 
ADD COLUMN max_runtime_sec INTEGER DEFAULT 3600,
ADD COLUMN internal_depth INTEGER DEFAULT 2,
ADD COLUMN follow_external BOOLEAN DEFAULT FALSE,
ADD COLUMN external_depth INTEGER DEFAULT 1;

-- Update existing records to have the default values
UPDATE crawls 
SET 
    max_runtime_sec = 3600,
    internal_depth = 2,
    follow_external = FALSE,
    external_depth = 1
WHERE 
    max_runtime_sec IS NULL 
    OR internal_depth IS NULL 
    OR follow_external IS NULL 
    OR external_depth IS NULL;
