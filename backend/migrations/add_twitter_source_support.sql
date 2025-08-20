-- Migration: Add Twitter/X Source Support
-- Description: Adds support for Twitter/X as a source type alongside website sources
-- Date: 2025-08-20

-- 1. Create source_type enum if it doesn't exist
DO $$ BEGIN
    CREATE TYPE source_type AS ENUM ('website', 'twitter');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Add source_type column to sources table
ALTER TABLE sources 
ADD COLUMN IF NOT EXISTS source_type source_type DEFAULT 'website';

-- 3. Add twitter_username column for Twitter sources
ALTER TABLE sources 
ADD COLUMN IF NOT EXISTS twitter_username text;

-- 4. Add constraint to ensure Twitter sources have username
ALTER TABLE sources 
ADD CONSTRAINT check_twitter_username 
CHECK (
    (source_type = 'twitter' AND twitter_username IS NOT NULL) OR 
    (source_type = 'website')
);

-- 5. Update existing sources to have source_type = 'website'
UPDATE sources 
SET source_type = 'website' 
WHERE source_type IS NULL;

-- 6. Add tweet_id column to articles table
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS tweet_id text;

-- 7. Add author_username column to articles table for tweet authors
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS author_username text;

-- 8. Add engagement metrics columns for tweets
ALTER TABLE articles 
ADD COLUMN IF NOT EXISTS like_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS retweet_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS reply_count integer DEFAULT 0;

-- 9. Create index for tweet_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_articles_tweet_id ON articles(tweet_id);

-- 10. Create index for author_username for filtering by author
CREATE INDEX IF NOT EXISTS idx_articles_author_username ON articles(author_username);

-- 11. Create index for source_type for filtering
CREATE INDEX IF NOT EXISTS idx_sources_source_type ON sources(source_type);

-- 12. Create unique constraint for twitter_username to prevent duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_twitter_username 
ON sources(twitter_username) 
WHERE source_type = 'twitter';

-- 13. Update the unique constraint on sources.url to be conditional
-- Drop the existing unique constraint if it exists
ALTER TABLE sources DROP CONSTRAINT IF EXISTS sources_url_key;

-- Add a new unique constraint that only applies to website sources
CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_url_website 
ON sources(url) 
WHERE source_type = 'website';

-- For Twitter sources, we'll use a convention like https://twitter.com/username
-- This allows us to keep the url field populated for both types

COMMENT ON COLUMN sources.source_type IS 'Type of source: website for traditional web scraping, twitter for Twitter/X accounts';
COMMENT ON COLUMN sources.twitter_username IS 'Twitter/X username without @ symbol, only for twitter source_type';
COMMENT ON COLUMN articles.tweet_id IS 'Original tweet ID from Twitter/X';
COMMENT ON COLUMN articles.author_username IS 'Twitter/X username of the tweet author';
COMMENT ON COLUMN articles.like_count IS 'Number of likes on the tweet';
COMMENT ON COLUMN articles.retweet_count IS 'Number of retweets';
COMMENT ON COLUMN articles.reply_count IS 'Number of replies to the tweet';