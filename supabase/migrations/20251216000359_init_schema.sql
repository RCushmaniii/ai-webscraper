-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- AAA Web Scraper Database Schema

-- 1. Create users table (extends auth.users)
CREATE TABLE users (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  is_admin BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create batches table
CREATE TABLE batches (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
  max_depth INTEGER DEFAULT 2,
  max_pages INTEGER DEFAULT 100,
  max_pages_per_crawl INTEGER DEFAULT 50,
  respect_robots_txt BOOLEAN DEFAULT TRUE,
  follow_external_links BOOLEAN DEFAULT FALSE,
  js_rendering BOOLEAN DEFAULT FALSE,
  rate_limit INTEGER DEFAULT 1,
  user_agent TEXT DEFAULT 'AAA Web Scraper Bot',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- 3. Create crawls table
CREATE TABLE crawls (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'in_progress', 'completed', 'failed')),
  error TEXT,
  max_depth INTEGER DEFAULT 2,
  max_pages INTEGER DEFAULT 100,
  respect_robots_txt BOOLEAN DEFAULT TRUE,
  follow_external_links BOOLEAN DEFAULT FALSE,
  js_rendering BOOLEAN DEFAULT FALSE,
  rate_limit INTEGER DEFAULT 1,
  user_agent TEXT DEFAULT 'AAA Web Scraper Bot',
  pages_crawled INTEGER DEFAULT 0,
  total_links INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- 4. Create pages table
CREATE TABLE pages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  meta_description TEXT,
  content_summary TEXT,
  status_code INTEGER,
  response_time INTEGER, -- in milliseconds
  content_type TEXT,
  content_length INTEGER,
  h1_tags TEXT[],
  h2_tags TEXT[],
  internal_links INTEGER DEFAULT 0,
  external_links INTEGER DEFAULT 0,
  images INTEGER DEFAULT 0,
  scripts INTEGER DEFAULT 0,
  stylesheets INTEGER DEFAULT 0,
  seo_score INTEGER,
  issues JSONB DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create links table
CREATE TABLE links (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE NOT NULL,
  source_page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  anchor_text TEXT,
  link_type TEXT CHECK (link_type IN ('internal', 'external', 'mailto', 'tel', 'file')),
  is_broken BOOLEAN DEFAULT FALSE,
  status_code INTEGER,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Create tasks table (for background job tracking)
CREATE TABLE tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE,
  batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
  task_type TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
  progress INTEGER DEFAULT 0,
  message TEXT,
  result JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE links ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies

-- Users policies
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can view all users" ON users
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE id = auth.uid() AND is_admin = true
    )
  );

-- Batches policies
CREATE POLICY "Users can view own batches" ON batches
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create batches" ON batches
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own batches" ON batches
  FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete own batches" ON batches
  FOR DELETE USING (user_id = auth.uid());

-- Crawls policies
CREATE POLICY "Users can view own crawls" ON crawls
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create crawls" ON crawls
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own crawls" ON crawls
  FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete own crawls" ON crawls
  FOR DELETE USING (user_id = auth.uid());

-- Pages policies
CREATE POLICY "Users can view pages from own crawls" ON pages
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = pages.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "System can insert pages" ON pages
  FOR INSERT WITH CHECK (true);

CREATE POLICY "System can update pages" ON pages
  FOR UPDATE USING (true);

-- Links policies
CREATE POLICY "Users can view links from own crawls" ON links
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = links.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "System can insert links" ON links
  FOR INSERT WITH CHECK (true);

-- Tasks policies
CREATE POLICY "Users can view own tasks" ON tasks
  FOR SELECT USING (
    (crawl_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = tasks.crawl_id AND crawls.user_id = auth.uid()
    ))
    OR
    (batch_id IS NOT NULL AND EXISTS (
      SELECT 1 FROM batches
      WHERE batches.id = tasks.batch_id AND batches.user_id = auth.uid()
    ))
  );

CREATE POLICY "System can manage tasks" ON tasks
  FOR ALL USING (true);

-- Create indexes for better performance
CREATE INDEX idx_batches_user_id ON batches(user_id);
CREATE INDEX idx_batches_status ON batches(status);
CREATE INDEX idx_crawls_batch_id ON crawls(batch_id);
CREATE INDEX idx_crawls_user_id ON crawls(user_id);
CREATE INDEX idx_crawls_status ON crawls(status);
CREATE INDEX idx_pages_crawl_id ON pages(crawl_id);
CREATE INDEX idx_pages_url ON pages(url);
CREATE INDEX idx_links_crawl_id ON links(crawl_id);
CREATE INDEX idx_links_source_page_id ON links(source_page_id);
CREATE INDEX idx_tasks_crawl_id ON tasks(crawl_id);
CREATE INDEX idx_tasks_batch_id ON tasks(batch_id);
CREATE INDEX idx_tasks_status ON tasks(status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_batches_updated_at BEFORE UPDATE ON batches
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crawls_updated_at BEFORE UPDATE ON crawls
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pages_updated_at BEFORE UPDATE ON pages
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
