-- Rollback Script for Schema Changes
-- WARNING: This will remove Twitter separation and revert to original schema
-- Only use if absolutely necessary!

-- ============================================================
-- BACKUP TWEETS DATA FIRST
-- ============================================================

-- Create a backup of tweets table before rollback
CREATE TABLE IF NOT EXISTS tweets_backup AS 
SELECT * FROM tweets;

-- ============================================================
-- ROLLBACK STEPS
-- ============================================================

-- Step 1: Move Twitter data back to articles table (if needed)
-- Only for tweets that don't already exist in articles
INSERT INTO articles (
    source_id,
    headline,
    url,
    full_content,
    summary,
    is_ai_related,
    tags,
    published_at,
    scraped_at,
    tweet_id,
    author_username,
    like_count,
    retweet_count,
    reply_count
)
SELECT 
    t.source_id,
    t.author_username || ': ' || LEFT(t.content, 100) || 
        CASE WHEN LENGTH(t.content) > 100 THEN '...' ELSE '' END as headline,
    'https://twitter.com/' || t.author_username || '/status/' || t.tweet_id as url,
    t.content as full_content,
    t.ai_summary as summary,
    t.is_ai_related,
    t.ai_tags as tags,
    DATE(t.published_at) as published_at,
    t.fetched_at as scraped_at,
    t.tweet_id,
    t.author_username,
    t.like_count,
    t.retweet_count,
    t.reply_count
FROM tweets t
LEFT JOIN articles a ON t.tweet_id = a.tweet_id
WHERE a.tweet_id IS NULL;  -- Only insert if not already in articles

-- Step 2: Drop the unified_content view (will be recreated without tweets table)
DROP VIEW IF EXISTS unified_content CASCADE;

-- Step 3: Recreate unified_content view without tweets table
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
    COALESCE(a.like_count, 0) as like_count,
    COALESCE(a.retweet_count, 0) as retweet_count,
    COALESCE(a.reply_count, 0) as reply_count,
    COALESCE(a.like_count, 0) + COALESCE(a.retweet_count, 0) * 2 as engagement_score,
    a.view_count,
    a.included_in_newsletter,
    a.image_url,
    a.author_username,
    a.tweet_id
FROM articles a
JOIN sources s ON a.source_id = s.id;

-- Step 4: Drop Twitter-specific objects (careful!)
-- Comment these out if you want to keep the tweets table for reference
-- DROP TABLE IF EXISTS tweets CASCADE;
-- DROP MATERIALIZED VIEW IF EXISTS daily_twitter_stats CASCADE;
-- DROP FUNCTION IF EXISTS get_twitter_thread CASCADE;
-- DROP FUNCTION IF EXISTS get_mixed_content_feed CASCADE;
-- DROP FUNCTION IF EXISTS refresh_twitter_stats CASCADE;

-- Step 5: Remove Twitter-specific columns from sources (optional)
-- ALTER TABLE sources DROP COLUMN IF EXISTS source_type;
-- ALTER TABLE sources DROP COLUMN IF EXISTS twitter_username;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Check that all tweets are back in articles
SELECT 
    'Tweets in backup' as description,
    COUNT(*) as count
FROM tweets_backup
UNION ALL
SELECT 
    'Twitter items in articles' as description,
    COUNT(*) as count
FROM articles
WHERE tweet_id IS NOT NULL;

-- Check unified_content still works
SELECT 
    content_type,
    COUNT(*) as count
FROM unified_content
GROUP BY content_type;

-- ============================================================
-- NOTES
-- ============================================================
-- 1. This script preserves the tweets_backup table for safety
-- 2. Uncomment the DROP statements only if you're sure
-- 3. The tweets table structure is preserved but could be dropped
-- 4. Run verification queries to ensure data integrity
-- 5. Test API endpoints after rollback