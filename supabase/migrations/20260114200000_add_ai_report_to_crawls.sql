-- Add AI Report columns to crawls table
-- This stores the AI-generated analysis report for each crawl

ALTER TABLE crawls
ADD COLUMN IF NOT EXISTS ai_report JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS ai_report_generated_at TIMESTAMPTZ DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN crawls.ai_report IS 'AI-generated analysis report with executive summary, priorities, and recommendations';
COMMENT ON COLUMN crawls.ai_report_generated_at IS 'Timestamp when the AI report was last generated';
