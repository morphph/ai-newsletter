-- Database schema for AI Newsletter Workflow
--
-- 1. News Sources Table
CREATE TABLE sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    url text NOT NULL,
    category text,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 2. Articles Table
CREATE TABLE articles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid REFERENCES sources(id) ON DELETE CASCADE,
    headline text NOT NULL,
    url text NOT NULL,
    published_at date NOT NULL,
    scraped_at timestamptz NOT NULL DEFAULT now(),
    full_content text,
    is_ai_related boolean NOT NULL DEFAULT false,
    summary text,
    included_in_newsletter boolean NOT NULL DEFAULT false
);

-- 3. Newsletters Table
CREATE TABLE newsletters (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sent_at timestamptz NOT NULL DEFAULT now(),
    subject text NOT NULL,
    content text NOT NULL
);

-- 4. Newsletter-Articles Join Table
CREATE TABLE newsletter_articles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    newsletter_id uuid REFERENCES newsletters(id) ON DELETE CASCADE,
    article_id uuid REFERENCES articles(id) ON DELETE CASCADE,
    position integer NOT NULL
);

-- 5. Users/Subscribers Table (Optional)
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL UNIQUE,
    subscribed_at timestamptz NOT NULL DEFAULT now(),
    unsubscribed_at timestamptz
);

-- Indexes for performance
CREATE INDEX idx_articles_published_at ON articles(published_at);
CREATE INDEX idx_articles_is_ai_related ON articles(is_ai_related);
CREATE INDEX idx_newsletter_articles_newsletter_id ON newsletter_articles(newsletter_id);
CREATE INDEX idx_newsletter_articles_article_id ON newsletter_articles(article_id); 