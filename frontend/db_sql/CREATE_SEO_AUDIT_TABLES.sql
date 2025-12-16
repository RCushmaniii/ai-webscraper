-- SEO Audit Tables for AAA Web Scraper
-- Run this in your Supabase SQL Editor to add SEO audit functionality

-- 1. Create comprehensive_audits table
CREATE TABLE comprehensive_audits (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE NOT NULL,
  overall_score INTEGER DEFAULT 0,
  priority_issues_count INTEGER DEFAULT 0,
  audit_data JSONB DEFAULT '{}',
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create seo_audits table (for individual page audits)
CREATE TABLE seo_audits (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE NOT NULL,
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE NOT NULL,
  title_length INTEGER,
  meta_description_length INTEGER,
  h1_count INTEGER DEFAULT 0,
  h2_count INTEGER DEFAULT 0,
  h3_count INTEGER DEFAULT 0,
  image_count INTEGER DEFAULT 0,
  images_without_alt INTEGER DEFAULT 0,
  internal_links_count INTEGER DEFAULT 0,
  external_links_count INTEGER DEFAULT 0,
  word_count INTEGER DEFAULT 0,
  page_load_time INTEGER,
  has_schema_markup BOOLEAN DEFAULT FALSE,
  schema_types TEXT[],
  seo_score INTEGER DEFAULT 0,
  issues JSONB DEFAULT '[]',
  recommendations JSONB DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create issues table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS issues (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE NOT NULL,
  page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
  issue_type TEXT NOT NULL,
  severity TEXT DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  description TEXT NOT NULL,
  url TEXT,
  context JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE comprehensive_audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE seo_audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE issues ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies for comprehensive_audits
CREATE POLICY "Users can view audits from own crawls" ON comprehensive_audits
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls 
      WHERE crawls.id = comprehensive_audits.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "System can manage comprehensive audits" ON comprehensive_audits
  FOR ALL USING (true);

-- Create RLS Policies for seo_audits
CREATE POLICY "Users can view seo audits from own crawls" ON seo_audits
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls 
      WHERE crawls.id = seo_audits.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "System can manage seo audits" ON seo_audits
  FOR ALL USING (true);

-- Create RLS Policies for issues
CREATE POLICY "Users can view issues from own crawls" ON issues
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls 
      WHERE crawls.id = issues.crawl_id AND crawls.user_id = auth.uid()
    )
  );

CREATE POLICY "System can manage issues" ON issues
  FOR ALL USING (true);

-- Create indexes for better performance
CREATE INDEX idx_comprehensive_audits_crawl_id ON comprehensive_audits(crawl_id);
CREATE INDEX idx_seo_audits_crawl_id ON seo_audits(crawl_id);
CREATE INDEX idx_seo_audits_page_id ON seo_audits(page_id);
CREATE INDEX idx_issues_crawl_id ON issues(crawl_id);
CREATE INDEX idx_issues_page_id ON issues(page_id);
CREATE INDEX idx_issues_severity ON issues(severity);

-- Create updated_at triggers
CREATE TRIGGER update_comprehensive_audits_updated_at BEFORE UPDATE ON comprehensive_audits
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seo_audits_updated_at BEFORE UPDATE ON seo_audits
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
