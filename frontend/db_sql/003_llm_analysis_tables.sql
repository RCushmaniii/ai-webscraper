-- ============================================
-- LLM Analysis Tables Migration
-- Run this in your Supabase SQL editor
-- ============================================

-- Enable pgvector extension for embeddings (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- Page Analysis Table
-- Stores per-page LLM analysis results
-- ============================================

CREATE TABLE IF NOT EXISTS page_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
    crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Analysis metadata
    analysis_level VARCHAR(20) NOT NULL DEFAULT 'basic',  -- 'basic', 'detailed', 'full'
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Tier 1: Basic analysis
    summary JSONB,              -- PageSummary model
    categorization JSONB,       -- PageCategorization model
    topics JSONB,               -- TopicExtraction model
    
    -- Tier 2: Detailed analysis
    content_quality JSONB,      -- ContentQualityAnalysis model
    seo_analysis JSONB,         -- SEOAnalysis model
    title_assessment JSONB,     -- TitleQualityAssessment model
    meta_suggestion JSONB,      -- MetaDescriptionSuggestion model
    
    -- Derived scores (for easy querying)
    content_score INTEGER,      -- 0-100
    seo_score INTEGER,          -- 0-100
    
    -- Processing metadata
    model_used VARCHAR(50),
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for page_analysis
CREATE INDEX IF NOT EXISTS idx_page_analysis_page ON page_analysis(page_id);
CREATE INDEX IF NOT EXISTS idx_page_analysis_crawl ON page_analysis(crawl_id);
CREATE INDEX IF NOT EXISTS idx_page_analysis_user ON page_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_page_analysis_content_score ON page_analysis(content_score);
CREATE INDEX IF NOT EXISTS idx_page_analysis_seo_score ON page_analysis(seo_score);

-- ============================================
-- Crawl Analysis Table
-- Stores per-crawl synthesis reports
-- ============================================

CREATE TABLE IF NOT EXISTS crawl_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Report type
    analysis_type VARCHAR(50) NOT NULL,  -- 'executive_summary', 'brand_voice', 'content_strategy'
    
    -- Report content
    content JSONB NOT NULL,     -- Full structured report
    
    -- Derived scores (for easy querying)
    overall_score INTEGER,
    
    -- Processing metadata
    model_used VARCHAR(50),
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for crawl_analysis
CREATE INDEX IF NOT EXISTS idx_crawl_analysis_crawl ON crawl_analysis(crawl_id);
CREATE INDEX IF NOT EXISTS idx_crawl_analysis_user ON crawl_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_crawl_analysis_type ON crawl_analysis(analysis_type);

-- ============================================
-- Page Embeddings Table
-- Stores vector embeddings for semantic search
-- ============================================

CREATE TABLE IF NOT EXISTS page_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
    crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Embedding configuration
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
    embedding_dimensions INTEGER NOT NULL DEFAULT 512,
    
    -- The embedding vector
    embedding VECTOR(512),
    
    -- Source text hash (to detect changes)
    content_hash VARCHAR(64),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (using IVFFlat for performance)
CREATE INDEX IF NOT EXISTS idx_page_embeddings_vector ON page_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_page_embeddings_page ON page_embeddings(page_id);
CREATE INDEX IF NOT EXISTS idx_page_embeddings_crawl ON page_embeddings(crawl_id);

-- ============================================
-- LLM Usage Tracking Table
-- Tracks all LLM API calls for cost management
-- ============================================

CREATE TABLE IF NOT EXISTS llm_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crawl_id UUID REFERENCES crawls(id) ON DELETE SET NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Request details
    task_type VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    
    -- Token usage
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    
    -- Cost
    cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    
    -- Status
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    duration_ms INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for usage tracking
CREATE INDEX IF NOT EXISTS idx_llm_usage_user ON llm_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_crawl ON llm_usage(crawl_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_task ON llm_usage(task_type);
CREATE INDEX IF NOT EXISTS idx_llm_usage_created ON llm_usage(created_at DESC);

-- ============================================
-- Image Analysis Table
-- Stores image audit results with alt text suggestions
-- ============================================

CREATE TABLE IF NOT EXISTS image_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
    crawl_id UUID REFERENCES crawls(id) ON DELETE CASCADE,
    
    -- Image details
    src_url TEXT NOT NULL,
    current_alt_text TEXT,
    
    -- AI suggestions
    suggested_alt_text TEXT,
    is_decorative BOOLEAN DEFAULT false,
    suggestion_confidence DECIMAL(3, 2),
    
    -- Audit results
    issues JSONB DEFAULT '[]',
    score INTEGER,  -- 0-100
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_image_analysis_page ON image_analysis(page_id);
CREATE INDEX IF NOT EXISTS idx_image_analysis_crawl ON image_analysis(crawl_id);

-- ============================================
-- Row Level Security Policies
-- ============================================

-- Enable RLS on all new tables
ALTER TABLE page_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawl_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE page_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_analysis ENABLE ROW LEVEL SECURITY;

-- Page Analysis policies
CREATE POLICY "Users can view own page analyses"
    ON page_analysis FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own page analyses"
    ON page_analysis FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own page analyses"
    ON page_analysis FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own page analyses"
    ON page_analysis FOR DELETE
    USING (auth.uid() = user_id);

-- Crawl Analysis policies
CREATE POLICY "Users can view own crawl analyses"
    ON crawl_analysis FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own crawl analyses"
    ON crawl_analysis FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own crawl analyses"
    ON crawl_analysis FOR DELETE
    USING (auth.uid() = user_id);

-- Page Embeddings policies
CREATE POLICY "Users can view own embeddings"
    ON page_embeddings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own embeddings"
    ON page_embeddings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own embeddings"
    ON page_embeddings FOR DELETE
    USING (auth.uid() = user_id);

-- LLM Usage policies
CREATE POLICY "Users can view own usage"
    ON llm_usage FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own usage"
    ON llm_usage FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Image Analysis policies (inherit from page ownership via crawl)
CREATE POLICY "Users can view own image analyses"
    ON image_analysis FOR SELECT
    USING (
        crawl_id IN (
            SELECT id FROM crawls WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert image analyses for own crawls"
    ON image_analysis FOR INSERT
    WITH CHECK (
        crawl_id IN (
            SELECT id FROM crawls WHERE user_id = auth.uid()
        )
    );

-- ============================================
-- Helper Functions
-- ============================================

-- Function to get total LLM cost for a crawl
CREATE OR REPLACE FUNCTION get_crawl_llm_cost(p_crawl_id UUID)
RETURNS DECIMAL(10, 6) AS $$
    SELECT COALESCE(SUM(cost_usd), 0)
    FROM llm_usage
    WHERE crawl_id = p_crawl_id;
$$ LANGUAGE SQL STABLE;

-- Function to get user's total LLM cost for a period
CREATE OR REPLACE FUNCTION get_user_llm_cost(
    p_user_id UUID,
    p_start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
    p_end_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS DECIMAL(10, 6) AS $$
    SELECT COALESCE(SUM(cost_usd), 0)
    FROM llm_usage
    WHERE user_id = p_user_id
    AND created_at BETWEEN p_start_date AND p_end_date;
$$ LANGUAGE SQL STABLE;

-- Function to find similar pages using embeddings
CREATE OR REPLACE FUNCTION find_similar_pages(
    p_page_id UUID,
    p_crawl_id UUID,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    page_id UUID,
    similarity FLOAT
) AS $$
    SELECT 
        pe2.page_id,
        1 - (pe1.embedding <=> pe2.embedding) as similarity
    FROM page_embeddings pe1
    JOIN page_embeddings pe2 ON pe1.crawl_id = pe2.crawl_id
    WHERE pe1.page_id = p_page_id
    AND pe2.page_id != p_page_id
    AND pe1.crawl_id = p_crawl_id
    ORDER BY pe1.embedding <=> pe2.embedding
    LIMIT p_limit;
$$ LANGUAGE SQL STABLE;

-- ============================================
-- Triggers
-- ============================================

-- Update timestamp trigger for page_analysis
CREATE OR REPLACE FUNCTION update_page_analysis_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER page_analysis_updated
    BEFORE UPDATE ON page_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_page_analysis_timestamp();

-- ============================================
-- Views for easy querying
-- ============================================

-- View: Page analysis with page details
CREATE OR REPLACE VIEW page_analysis_details AS
SELECT
    pa.*,
    p.url,
    p.title,
    p.status_code,
    p.content_length
FROM page_analysis pa
JOIN pages p ON pa.page_id = p.id;

-- View: Crawl analysis summary
CREATE OR REPLACE VIEW crawl_analysis_summary AS
SELECT
    c.id as crawl_id,
    c.url,
    c.status,
    COUNT(DISTINCT pa.id) as pages_analyzed,
    AVG(pa.content_score) as avg_content_score,
    AVG(pa.seo_score) as avg_seo_score,
    SUM(lu.cost_usd) as total_llm_cost,
    MAX(ca.created_at) as last_report_at
FROM crawls c
LEFT JOIN page_analysis pa ON c.id = pa.crawl_id
LEFT JOIN llm_usage lu ON c.id = lu.crawl_id
LEFT JOIN crawl_analysis ca ON c.id = ca.crawl_id
GROUP BY c.id, c.url, c.status;

-- ============================================
-- Sample Queries (for reference)
-- ============================================

-- Get pages with low content scores
-- SELECT * FROM page_analysis_details 
-- WHERE content_score < 50 
-- ORDER BY content_score ASC;

-- Get crawl cost breakdown
-- SELECT task_type, COUNT(*) as calls, SUM(cost_usd) as total_cost
-- FROM llm_usage
-- WHERE crawl_id = 'your-crawl-id'
-- GROUP BY task_type
-- ORDER BY total_cost DESC;

-- Find duplicate content using embeddings
-- SELECT * FROM find_similar_pages('page-uuid', 'crawl-uuid', 10)
-- WHERE similarity > 0.9;