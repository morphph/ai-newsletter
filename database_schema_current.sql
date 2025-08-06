-- Current Database Schema for AI News App
-- This schema represents what the application actually uses

-- 1. Sources Table
CREATE TABLE IF NOT EXISTS sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    url text NOT NULL UNIQUE,
    category text,
    active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

-- 2. Articles Table
CREATE TABLE IF NOT EXISTS articles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid REFERENCES sources(id) ON DELETE CASCADE,
    headline text NOT NULL,
    url text NOT NULL UNIQUE,
    summary text,
    full_content text,
    is_ai_related boolean NOT NULL DEFAULT false,
    tags text[],
    image_url text,
    published_at date NOT NULL,
    scraped_at timestamp with time zone DEFAULT now(),
    view_count integer DEFAULT 0,
    included_in_newsletter boolean DEFAULT false
);

-- 3. Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_is_ai_related ON articles(is_ai_related);
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_sources_active ON sources(active);
CREATE INDEX IF NOT EXISTS idx_sources_category ON sources(category);

-- Note: The following tables exist in the database but are no longer used:
-- - newsletters (can be dropped if not needed for historical data)
-- - newsletter_articles (can be dropped if not needed for historical data)
-- - users (not used in current app)