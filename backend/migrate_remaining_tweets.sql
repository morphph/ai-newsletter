-- Migration: Move remaining Twitter items from articles to tweets table
-- Generated at: 2025-08-22
-- Description: Migrates 2 remaining Twitter items that were not previously migrated

-- First, let's check what Twitter data is still in articles table
SELECT 
    a.id,
    a.tweet_id,
    a.author_username,
    a.headline,
    a.full_content,
    a.source_id,
    s.name as source_name,
    s.source_type
FROM articles a
JOIN sources s ON a.source_id = s.id
WHERE a.tweet_id IS NOT NULL;

-- Migrate the remaining Twitter data to tweets table
-- Using INSERT ... ON CONFLICT to handle any duplicates safely
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
    COALESCE(a.author_username, 'unknown'),  -- Handle null author
    COALESCE(a.full_content, a.headline),    -- Use full_content or headline as content
    COALESCE(a.like_count, 0),
    COALESCE(a.retweet_count, 0),
    COALESCE(a.reply_count, 0),
    a.is_ai_related,
    a.summary,
    a.tags,
    a.published_at::timestamp with time zone,
    a.scraped_at,
    a.included_in_newsletter
FROM articles a
JOIN sources s ON a.source_id = s.id
WHERE a.tweet_id IS NOT NULL
ON CONFLICT (tweet_id) DO UPDATE SET
    -- Update engagement metrics if tweet already exists
    like_count = EXCLUDED.like_count,
    retweet_count = EXCLUDED.retweet_count,
    reply_count = EXCLUDED.reply_count,
    updated_at = now();

-- After migration, optionally delete Twitter items from articles table
-- IMPORTANT: Only run this after verifying the migration was successful
-- DELETE FROM articles WHERE tweet_id IS NOT NULL;

-- Verify the migration
SELECT 
    'Articles with tweet_id' as type,
    COUNT(*) as count
FROM articles 
WHERE tweet_id IS NOT NULL
UNION ALL
SELECT 
    'Tweets in tweets table' as type,
    COUNT(*) as count
FROM tweets;