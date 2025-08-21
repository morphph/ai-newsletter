-- Migration: Separate Twitter Content from Articles
-- Description: Creates dedicated tweets table and unified content view
-- Date: 2025-08-21

-- 1. Create tweets table for Twitter-specific content
CREATE TABLE IF NOT EXISTS tweets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid REFERENCES sources(id) ON DELETE CASCADE,
    tweet_id text UNIQUE NOT NULL,
    author_username text NOT NULL,
    content text NOT NULL,
    
    -- Engagement metrics
    like_count integer DEFAULT 0,
    retweet_count integer DEFAULT 0,
    reply_count integer DEFAULT 0,
    view_count integer DEFAULT 0,
    bookmark_count integer DEFAULT 0,
    
    -- Tweet metadata
    is_reply boolean DEFAULT false,
    is_retweet boolean DEFAULT false,
    is_quote_tweet boolean DEFAULT false,
    has_media boolean DEFAULT false,
    media_urls text[],
    hashtags text[],
    mentions text[],
    urls text[],
    
    -- Thread information
    conversation_id text,
    in_reply_to_tweet_id text,
    quoted_tweet_id text,
    thread_position integer,
    
    -- Quoted tweet content (denormalized for performance)
    quoted_tweet_content text,
    quoted_tweet_author text,
    
    -- AI processing fields
    is_ai_related boolean DEFAULT false,
    ai_summary text,
    ai_tags text[],
    ai_relevance_score float,
    ai_processed_at timestamp with time zone,
    
    -- Timestamps
    published_at timestamp with time zone NOT NULL,
    fetched_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    
    -- Newsletter and display
    included_in_newsletter boolean DEFAULT false,
    newsletter_date date,
    display_priority integer DEFAULT 0
);

-- 2. Create indexes for efficient querying
CREATE INDEX idx_tweets_source_id ON tweets(source_id);
CREATE INDEX idx_tweets_tweet_id ON tweets(tweet_id);
CREATE INDEX idx_tweets_author_username ON tweets(author_username);
CREATE INDEX idx_tweets_published_at ON tweets(published_at);
CREATE INDEX idx_tweets_is_ai_related ON tweets(is_ai_related) WHERE is_ai_related = true;
CREATE INDEX idx_tweets_conversation_id ON tweets(conversation_id) WHERE conversation_id IS NOT NULL;
CREATE INDEX idx_tweets_engagement ON tweets((like_count + retweet_count * 2));
CREATE INDEX idx_tweets_fetched_at ON tweets(fetched_at);
CREATE INDEX idx_tweets_newsletter ON tweets(included_in_newsletter, newsletter_date);

-- 3. Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_tweets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tweets_updated_at_trigger
BEFORE UPDATE ON tweets
FOR EACH ROW
EXECUTE FUNCTION update_tweets_updated_at();

-- 4. Migrate existing Twitter data from articles to tweets
INSERT INTO tweets (
    source_id,
    tweet_id,
    author_username,
    content,
    like_count,
    retweet_count,
    reply_count,
    is_ai_related,
    ai_summary,
    ai_tags,
    published_at,
    fetched_at,
    included_in_newsletter
)
SELECT 
    a.source_id,
    a.tweet_id,
    a.author_username,
    a.full_content,
    COALESCE(a.like_count, 0),
    COALESCE(a.retweet_count, 0),
    COALESCE(a.reply_count, 0),
    a.is_ai_related,
    a.summary,
    a.tags,
    a.published_at,
    a.scraped_at,
    a.included_in_newsletter
FROM articles a
JOIN sources s ON a.source_id = s.id
WHERE s.source_type = 'twitter' 
  AND a.tweet_id IS NOT NULL
ON CONFLICT (tweet_id) DO NOTHING;

-- 5. Create unified content view for backward compatibility
CREATE OR REPLACE VIEW unified_content AS
SELECT 
    'article' as content_type,
    a.id,
    a.source_id,
    s.name as source_name,
    s.source_type,
    a.headline,
    a.url,
    a.full_content as content,
    a.summary,
    a.is_ai_related,
    a.tags,
    a.published_at,
    a.scraped_at as fetched_at,
    0 as like_count,
    0 as retweet_count,
    0 as reply_count,
    0 as engagement_score,
    a.view_count,
    a.included_in_newsletter,
    a.image_url,
    NULL::text as author_username,
    NULL::text as tweet_id
FROM articles a
JOIN sources s ON a.source_id = s.id
WHERE s.source_type != 'twitter' OR s.source_type IS NULL

UNION ALL

SELECT 
    'tweet' as content_type,
    t.id,
    t.source_id,
    s.name as source_name,
    s.source_type,
    t.author_username || ': ' || LEFT(t.content, 100) || 
        CASE WHEN LENGTH(t.content) > 100 THEN '...' ELSE '' END as headline,
    'https://twitter.com/' || t.author_username || '/status/' || t.tweet_id as url,
    t.content,
    t.ai_summary as summary,
    t.is_ai_related,
    t.ai_tags as tags,
    t.published_at,
    t.fetched_at,
    t.like_count,
    t.retweet_count,
    t.reply_count,
    (t.like_count + t.retweet_count * 2 + t.reply_count) as engagement_score,
    t.view_count,
    t.included_in_newsletter,
    t.media_urls[1] as image_url,  -- First media URL if available
    t.author_username,
    t.tweet_id
FROM tweets t
JOIN sources s ON t.source_id = s.id;

-- 6. Create function to get mixed content feed
CREATE OR REPLACE FUNCTION get_mixed_content_feed(
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0,
    p_ai_only boolean DEFAULT false,
    p_start_date date DEFAULT NULL,
    p_end_date date DEFAULT NULL
)
RETURNS TABLE (
    content_type text,
    id uuid,
    source_name text,
    headline text,
    url text,
    summary text,
    is_ai_related boolean,
    published_at timestamp with time zone,
    engagement_score integer
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        uc.content_type,
        uc.id,
        uc.source_name,
        uc.headline,
        uc.url,
        uc.summary,
        uc.is_ai_related,
        uc.published_at,
        uc.engagement_score
    FROM unified_content uc
    WHERE 
        (NOT p_ai_only OR uc.is_ai_related = true)
        AND (p_start_date IS NULL OR DATE(uc.published_at) >= p_start_date)
        AND (p_end_date IS NULL OR DATE(uc.published_at) <= p_end_date)
    ORDER BY 
        uc.published_at DESC,
        uc.engagement_score DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 7. Create function to get Twitter threads
CREATE OR REPLACE FUNCTION get_twitter_thread(p_conversation_id text)
RETURNS TABLE (
    tweet_id text,
    author_username text,
    content text,
    thread_position integer,
    published_at timestamp with time zone,
    like_count integer,
    retweet_count integer
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.tweet_id,
        t.author_username,
        t.content,
        t.thread_position,
        t.published_at,
        t.like_count,
        t.retweet_count
    FROM tweets t
    WHERE t.conversation_id = p_conversation_id
    ORDER BY t.thread_position, t.published_at;
END;
$$ LANGUAGE plpgsql;

-- 8. Create materialized view for daily Twitter stats
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_twitter_stats AS
SELECT 
    DATE(t.published_at) as date,
    s.name as source_name,
    s.twitter_username,
    COUNT(*) as tweet_count,
    COUNT(*) FILTER (WHERE t.is_ai_related) as ai_tweet_count,
    AVG(t.like_count) as avg_likes,
    AVG(t.retweet_count) as avg_retweets,
    MAX(t.like_count) as max_likes,
    MAX(t.retweet_count) as max_retweets,
    SUM(t.like_count + t.retweet_count * 2) as total_engagement
FROM tweets t
JOIN sources s ON t.source_id = s.id
GROUP BY DATE(t.published_at), s.name, s.twitter_username;

CREATE UNIQUE INDEX idx_daily_twitter_stats_date_source 
ON daily_twitter_stats(date, source_name);

-- 9. Create function to refresh Twitter stats
CREATE OR REPLACE FUNCTION refresh_twitter_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_twitter_stats;
END;
$$ LANGUAGE plpgsql;

-- 10. Comments for documentation
COMMENT ON TABLE tweets IS 'Stores Twitter/X posts with full metadata and engagement metrics';
COMMENT ON COLUMN tweets.tweet_id IS 'Unique Twitter ID for the tweet';
COMMENT ON COLUMN tweets.conversation_id IS 'ID linking tweets in the same thread/conversation';
COMMENT ON COLUMN tweets.ai_relevance_score IS 'AI-calculated relevance score (0-1) for ranking';
COMMENT ON COLUMN tweets.display_priority IS 'Manual priority override for newsletter/display ordering';
COMMENT ON VIEW unified_content IS 'Unified view combining articles and tweets for backward compatibility';
COMMENT ON FUNCTION get_mixed_content_feed IS 'Returns mixed content from both articles and tweets with filtering options';

-- 11. Grant appropriate permissions (adjust based on your users)
-- GRANT SELECT ON tweets TO your_api_user;
-- GRANT SELECT ON unified_content TO your_api_user;
-- GRANT EXECUTE ON FUNCTION get_mixed_content_feed TO your_api_user;
-- GRANT EXECUTE ON FUNCTION get_twitter_thread TO your_api_user;