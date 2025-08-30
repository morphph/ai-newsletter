# AI Newsletter Sources - Categorized

## Setup Instructions

To enable source categorization, run this SQL command in your Supabase SQL Editor:

```sql
-- Add category column to sources table
ALTER TABLE sources ADD COLUMN IF NOT EXISTS category text;

-- Update existing sources with categories
UPDATE sources SET category = CASE
    WHEN name IN (
        'OpenAI News',
        'Anthropic News',
        'Anthropic Release Notes',
        'Anthropic Research',
        'Google AI Blog',
        'Google Developers Blog',
        'Google DeepMind Blog',
        'Google Gemini Developer Blog'
    ) THEN 'Official AI Companies'
    WHEN name IN (
        'Simon Willison',
        'Hacker News',
        'Reuters AI News'
    ) THEN 'AI Researchers & Thought Leaders'
    WHEN name IN (
        'Firecrawl Blog'
    ) THEN 'AI Tools'
    ELSE category
END;
```

## Current Sources by Category

### Official AI Companies
1. **OpenAI News** - https://openai.com/news/
2. **Anthropic News** - https://www.anthropic.com/news
3. **Anthropic Release Notes** - https://docs.anthropic.com/en/release-notes/overview
4. **Anthropic Research** - https://www.anthropic.com/research *(NEW)*
5. **Google AI Blog** - https://blog.google/technology/ai/
6. **Google Developers Blog** - https://blog.google/technology/developers/
7. **Google DeepMind Blog** - https://blog.google/technology/google-deepmind/
8. **Google Gemini Developer Blog** - https://developers.googleblog.com/en/search/?product_categories=Gemini

### AI Researchers & Thought Leaders
1. **Simon Willison** - https://simonwillison.net/
2. **Hacker News** - https://news.ycombinator.com/
3. **Reuters AI News** - https://www.reuters.com/technology/artificial-intelligence/

### AI Tools
1. **Firecrawl Blog** - https://www.firecrawl.dev/blog/

## Changes Made
- ✅ Removed: AI News by Buttondown (https://buttondown.email/ainews/archive/)
- ✅ Added: Anthropic Research (https://www.anthropic.com/research)
- ✅ Categorized all sources into three categories

## Using Categories in the Workflow

Once the category column is added, you can:

1. Filter sources by category when processing
2. Group newsletter content by category
3. Prioritize certain categories
4. Generate category-specific newsletters

Example query to get sources by category:
```sql
SELECT * FROM sources 
WHERE category = 'Official AI Companies' 
AND active = true
ORDER BY name;
```