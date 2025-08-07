-- Migration: Add processing stages and enhanced tracking to articles table
-- Run this in your Supabase SQL Editor

-- 1. Add processing_stage enum type
CREATE TYPE processing_stage AS ENUM ('pending_enrichment', 'pending_summary', 'completed');

-- 2. Add new columns to articles table
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS processing_stage processing_stage DEFAULT 'completed',
ADD COLUMN IF NOT EXISTS crawl_batch_id uuid,
ADD COLUMN IF NOT EXISTS actual_published_date timestamp with time zone,
ADD COLUMN IF NOT EXISTS confidence text,
ADD COLUMN IF NOT EXISTS error_message text,
ADD COLUMN IF NOT EXISTS retry_count integer DEFAULT 0;

-- 3. Add indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_articles_processing_stage ON articles(processing_stage);
CREATE INDEX IF NOT EXISTS idx_articles_crawl_batch_id ON articles(crawl_batch_id);
CREATE INDEX IF NOT EXISTS idx_articles_actual_published_date ON articles(actual_published_date);

-- 4. Update existing articles to have 'completed' processing_stage
UPDATE articles 
SET processing_stage = 'completed' 
WHERE processing_stage IS NULL;

-- 5. Create source_stats table for monitoring
CREATE TABLE IF NOT EXISTS source_stats (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid REFERENCES sources(id) ON DELETE CASCADE,
    crawl_date date NOT NULL,
    success_count integer DEFAULT 0,
    failure_count integer DEFAULT 0,
    articles_found integer DEFAULT 0,
    new_articles integer DEFAULT 0,
    last_error text,
    created_at timestamp with time zone DEFAULT now()
);

-- 6. Add unique constraint for source stats per day
CREATE UNIQUE INDEX IF NOT EXISTS idx_source_stats_unique 
ON source_stats(source_id, crawl_date);

-- 7. Create a view for monitoring article processing
CREATE OR REPLACE VIEW article_processing_status AS
SELECT 
    processing_stage,
    COUNT(*) as count,
    DATE(scraped_at) as crawl_date
FROM articles
GROUP BY processing_stage, DATE(scraped_at)
ORDER BY crawl_date DESC, processing_stage;

-- 8. Add function to clean up old incomplete articles (older than 7 days)
CREATE OR REPLACE FUNCTION cleanup_incomplete_articles()
RETURNS void AS $$
BEGIN
    DELETE FROM articles 
    WHERE processing_stage != 'completed' 
    AND scraped_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- 9. Add trigger to update actual_published_date if not set
CREATE OR REPLACE FUNCTION set_actual_published_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.actual_published_date IS NULL THEN
        NEW.actual_published_date = NEW.published_at::timestamp with time zone;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_actual_published_date
BEFORE INSERT OR UPDATE ON articles
FOR EACH ROW
EXECUTE FUNCTION set_actual_published_date();

-- 10. Add function to get today's articles with proper timezone handling
CREATE OR REPLACE FUNCTION get_todays_articles(tz text DEFAULT 'UTC')
RETURNS TABLE (
    id uuid,
    headline text,
    url text,
    source_name text,
    published_at date,
    processing_stage processing_stage
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.headline,
        a.url,
        s.name as source_name,
        a.published_at,
        a.processing_stage
    FROM articles a
    JOIN sources s ON a.source_id = s.id
    WHERE DATE(a.actual_published_date AT TIME ZONE tz) = CURRENT_DATE
    ORDER BY a.actual_published_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Example queries to verify the migration:
-- SELECT * FROM article_processing_status;
-- SELECT * FROM get_todays_articles('America/New_York');
-- SELECT processing_stage, COUNT(*) FROM articles GROUP BY processing_stage;