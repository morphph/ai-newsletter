# Twitter/X Integration Setup Guide

## Overview
This guide explains how to set up Twitter/X as a second source type for fetching AI-related content from specific Twitter accounts.

## Prerequisites

### 1. Twitter API Key
You need to obtain an API key from [twitterapi.io](https://twitterapi.io):
1. Sign up for an account at https://twitterapi.io
2. Get your API key from the dashboard
3. Add it to your environment variables

### 2. Environment Configuration
Add the following to your `.env` file:

```bash
# Twitter API Configuration
TWITTER_API_KEY=your-twitter-api-key-here
```

## Database Setup

### 1. Run the Migration
Apply the database migration to add Twitter support:

```bash
# Connect to your database and run:
psql -d your_database -f backend/migrations/add_twitter_source_support.sql
```

This migration adds:
- `source_type` enum field to distinguish between 'website' and 'twitter' sources
- `twitter_username` field for storing Twitter handles
- `tweet_id`, `author_username`, and engagement metrics to the articles table

## Adding Twitter Sources

### Quick Setup: Add Pre-configured Sources

The system includes 40+ carefully curated AI Twitter accounts. Simply run:

```bash
# Add all 40+ default AI Twitter sources
python scripts/manage_twitter_sources.py add-defaults
```

This adds accounts in these categories:
- **AI Researchers** (8 accounts): Karpathy, LeCun, Hinton, etc.
- **AI Leaders** (6 accounts): Sam Altman, Demis Hassabis, Andrew Ng, etc.
- **AI Critics** (4 accounts): Gary Marcus, Emily Bender, Timnit Gebru, etc.
- **AI Educators** (5 accounts): Ethan Mollick, Lex Fridman, etc.
- **AI Engineers** (7 accounts): Simon Willison, Jason Liu, etc.
- **AI Companies** (8 accounts): OpenAI, DeepMind, Anthropic, etc.
- **AI News** (3 accounts): The AI Edge, MIT CSAIL, etc.

### Managing Sources

```bash
# List all Twitter sources
python scripts/manage_twitter_sources.py list

# Test fetching from a source
python scripts/manage_twitter_sources.py test @karpathy --limit 5

# Deactivate a source (stop fetching tweets)
python scripts/manage_twitter_sources.py deactivate @garymarcus

# Reactivate a source
python scripts/manage_twitter_sources.py activate @garymarcus

# View statistics
python scripts/manage_twitter_sources.py stats
```

### Using the API

```bash
# Create using twitter_input field (accepts URLs or handles)
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sam Altman",
    "source_type": "twitter",
    "twitter_input": "https://twitter.com/sama",
    "category": "AI Leaders",
    "active": true
  }'

# Or using direct username
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Andrej Karpathy",
    "source_type": "twitter",
    "twitter_username": "karpathy",
    "category": "AI Researchers",
    "active": true
  }'

# Get all Twitter sources
curl http://localhost:8000/api/sources/twitter

# Toggle source status
curl -X PATCH http://localhost:8000/api/sources/{source_id}/toggle
```

## Pre-configured Twitter Accounts (40+ Sources)

The `add-defaults` command adds these curated accounts:

### AI Researchers (8)
- @karpathy - Andrej Karpathy
- @ylecun - Yann LeCun  
- @geoffreyhinton - Geoffrey Hinton
- @drjimfan - Jim Fan (NVIDIA)
- @goodfellow_ian - Ian Goodfellow
- @fchollet - François Chollet
- @hardmaru - David Ha
- @OriolVinyalsML - Oriol Vinyals

### AI Leaders (6)
- @sama - Sam Altman (OpenAI)
- @demishassabis - Demis Hassabis (DeepMind)
- @AndrewYNg - Andrew Ng
- @gdb - Greg Brockman (OpenAI)
- @ilyasut - Ilya Sutskever
- @clementdelangue - Clement Delangue (HuggingFace)

### AI Critics & Ethics (4)
- @GaryMarcus - Gary Marcus
- @emilymbender - Emily M. Bender
- @timnitGebru - Timnit Gebru
- @mmitchell_ai - Margaret Mitchell

### AI Educators (5)
- @emollick - Ethan Mollick
- @lexfridman - Lex Fridman
- @rasbt - Sebastian Raschka
- @_akhaliq - AK
- @karinanguyen_ - Karina Nguyen

### AI Engineers (7)
- @simonw - Simon Willison
- @jxnlco - Jason Liu
- @aparnadhinak - Aparna Dhinakaran
- @vboykis - Vicki Boykis
- @swyx - Shawn Wang
- @transitive_bs - Logan Kilpatrick
- @alvinfoo - Alvin Foo

### AI Companies (8)
- @OpenAI - OpenAI
- @DeepMind - DeepMind
- @AnthropicAI - Anthropic
- @MistralAI - Mistral AI
- @StabilityAI - Stability AI
- @weights_biases - Weights & Biases
- @huggingface - Hugging Face
- @CohereAI - Cohere

### AI News (3)
- @TheAIEdge - The AI Edge
- @MIT_CSAIL - MIT CSAIL
- @DeepLearningAI - DeepLearning.AI

## How It Works

### 1. Data Collection Pipeline
The enhanced news crawler now handles both website and Twitter sources:

1. **Stage 1: Collect Content**
   - For websites: Scrapes homepage using Firecrawl
   - For Twitter: Fetches recent tweets using TwitterAPI

2. **Stage 2: Enrich Content**
   - For websites: Fetches full article content
   - For Twitter: Already has full content (tweets)

3. **Stage 3: Summarize**
   - Uses OpenAI to generate summaries
   - Different prompts for tweets vs articles

### 2. Tweet Processing
- Filters out retweets and replies to get original content
- Checks AI relevance using OpenAI
- Stores engagement metrics (likes, retweets, replies)
- Converts tweets to article format for unified display

### 3. Running the Crawler
```bash
# Run the enhanced crawler (processes both websites and Twitter)
python backend/src/workers/news_crawler_v2.py

# Run with specific options
python backend/src/workers/news_crawler_v2.py --stage all
python backend/src/workers/news_crawler_v2.py --resume
```

## API Endpoints

### Sources Management
- `GET /api/sources` - Get all sources (with optional `source_type` filter)
- `GET /api/sources/twitter` - Get only Twitter sources
- `GET /api/sources/websites` - Get only website sources
- `POST /api/sources` - Create a new source
- `PATCH /api/sources/{id}/toggle` - Toggle source active status

### Articles
- Articles from Twitter sources include:
  - `tweet_id` - Original tweet ID
  - `author_username` - Twitter handle
  - `like_count`, `retweet_count`, `reply_count` - Engagement metrics
  - `source_type` - Identifies if article is from Twitter or website

## Troubleshooting

### Common Issues

1. **Twitter API Rate Limits**
   - The twitterapi.io service has rate limits
   - The crawler includes delays between requests
   - Consider spreading Twitter source processing over time

2. **Missing Tweets**
   - The system filters for AI-related content
   - Only fetches original tweets (no retweets/replies)
   - Focuses on yesterday's tweets by default

3. **Database Errors**
   - Ensure migration has been run
   - Check that existing sources have `source_type='website'`
   - Verify unique constraints are properly set

## Best Practices

1. **Source Selection**
   - Choose accounts that frequently post AI-related content
   - Avoid accounts that mainly retweet
   - Consider categorizing sources for better organization

2. **Performance**
   - Limit the number of active Twitter sources
   - Run crawler during off-peak hours
   - Monitor API usage and costs

3. **Content Quality**
   - Regularly review AI relevance filtering
   - Adjust OpenAI prompts if needed
   - Monitor summary quality for tweets vs articles