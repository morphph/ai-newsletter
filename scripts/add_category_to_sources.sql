-- Add category column to sources table
ALTER TABLE sources 
ADD COLUMN category text;

-- Update existing sources with categories
UPDATE sources SET category = 'Official AI Companies' WHERE name IN (
    'OpenAI News',
    'Anthropic News',
    'Anthropic Release Notes',
    'Anthropic Research',
    'Google AI Blog',
    'Google Developers Blog',
    'Google DeepMind Blog',
    'Google Gemini Developer Blog'
);

UPDATE sources SET category = 'AI Researchers & Thought Leaders' WHERE name IN (
    'Simon Willison',
    'Hacker News',
    'Reuters AI News'
);

UPDATE sources SET category = 'AI Tools' WHERE name IN (
    'Firecrawl Blog'
);