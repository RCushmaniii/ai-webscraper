-- Add missing DELETE policies for RLS-enabled tables
-- These tables have RLS enabled but no DELETE policies, causing 500 errors
-- Only adding policies for tables that actually exist in the database

-- Pages table DELETE policy (if exists and policy doesn't exist)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'pages') 
       AND NOT EXISTS (SELECT FROM pg_policies WHERE tablename = 'pages' AND policyname = 'Users can delete their own pages') THEN
        EXECUTE 'CREATE POLICY "Users can delete their own pages" ON pages
          FOR DELETE USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = pages.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
    END IF;
END $$;

-- Links table DELETE policy (if exists and policy doesn't exist)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'links') 
       AND NOT EXISTS (SELECT FROM pg_policies WHERE tablename = 'links' AND policyname = 'Users can delete their own links') THEN
        EXECUTE 'CREATE POLICY "Users can delete their own links" ON links
          FOR DELETE USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = links.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
    END IF;
END $$;

-- Issues table DELETE policy (if exists and policy doesn't exist)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'issues') 
       AND NOT EXISTS (SELECT FROM pg_policies WHERE tablename = 'issues' AND policyname = 'Users can delete their own issues') THEN
        EXECUTE 'CREATE POLICY "Users can delete their own issues" ON issues
          FOR DELETE USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = issues.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
    END IF;
END $$;

-- Summaries table DELETE policy (if exists and policy doesn't exist)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'summaries') 
       AND NOT EXISTS (SELECT FROM pg_policies WHERE tablename = 'summaries' AND policyname = 'Users can delete their own summaries') THEN
        EXECUTE 'CREATE POLICY "Users can delete their own summaries" ON summaries
          FOR DELETE USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = summaries.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
    END IF;
END $$;

-- Check which tables actually exist and create missing ones if needed
DO $$
BEGIN
    -- Create issues table if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'issues') THEN
        EXECUTE 'CREATE TABLE issues (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
            page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
            issue_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT ''medium'',
            message TEXT NOT NULL,
            details JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )';
        
        -- Enable RLS and add policies for issues table
        EXECUTE 'ALTER TABLE issues ENABLE ROW LEVEL SECURITY';
        EXECUTE 'CREATE POLICY "Users can view their own issues" ON issues
          FOR SELECT USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = issues.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
        EXECUTE 'CREATE POLICY "Users can delete their own issues" ON issues
          FOR DELETE USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = issues.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
    END IF;
    
    -- Create summaries table if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'summaries') THEN
        EXECUTE 'CREATE TABLE summaries (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
            crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
            content TEXT,
            word_count INT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )';
        
        -- Enable RLS and add policies for summaries table
        EXECUTE 'ALTER TABLE summaries ENABLE ROW LEVEL SECURITY';
        EXECUTE 'CREATE POLICY "Users can view their own summaries" ON summaries
          FOR SELECT USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = summaries.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
        EXECUTE 'CREATE POLICY "Users can delete their own summaries" ON summaries
          FOR DELETE USING (
            EXISTS (
              SELECT 1 FROM crawls
              WHERE crawls.id = summaries.crawl_id
              AND crawls.user_id = auth.uid()
            )
          )';
    END IF;
END $$;
