# AI News Aggregator - Optimized Data Flow Diagram

## System Overview
```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI NEWS AGGREGATOR SYSTEM                        │
│                         (Daily @ 9am)                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Target Date =       │
                    │   Yesterday (Aug 21)  │
                    └───────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
```

## Data Sources Flow

### 1️⃣ WEBSITE FLOW (Hybrid Approach)
```
┌─────────────────────────────────────────────────────────────────────┐
│                        WEBSITE SOURCES                               │
│              (Anthropic, TechCrunch, Verge, etc.)                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   🔥 Firecrawl API    │
                    │   Scrape Homepage     │
                    │   (1 API call/site)   │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Extract Article Links│
                    │  (20-30 articles)     │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🐍 Python Date Filter│
                    │  • Check URL patterns │
                    │  • "yesterday" text   │
                    │  • Date extraction    │
                    │  (0 API calls)        │
                    └───────────────────────┘
                                │
                        [8 articles match]
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🤖 GPT Batch Eval    │
                    │  "Which are AI/LLM?"  │
                    │  (1 GPT API call)     │
                    └───────────────────────┘
                                │
                        [3 AI articles]
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🔥 Firecrawl Full    │
                    │  Scrape 3 articles    │
                    │  (3 API calls)        │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  💾 Store in Supabase │
                    │  is_ai_related: true  │
                    │  published_at: Aug 21 │
                    └───────────────────────┘
```

### 2️⃣ TWITTER/X FLOW (Optimized)
```
┌─────────────────────────────────────────────────────────────────────┐
│                        TWITTER SOURCES                               │
│              (@GeminiApp, @AnthropicAI, etc.)                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🐦 Twitter API       │
                    │  Fetch last 200 tweets│
                    │  Filter: Aug 21 only  │
                    └───────────────────────┘
                                │
                        [15 tweets from Aug 21]
                                │
                                ▼
                    ┌───────────────────────┐
                    │  🤖 GPT Batch Eval    │
                    │  "Which are AI/LLM?"  │
                    │  (1 GPT API call)     │
                    └───────────────────────┘
                                │
                        [6 AI tweets]
                                │
                                ▼
                    ┌───────────────────────┐
                    │  💾 Store in Supabase │
                    │  is_ai_related: true  │
                    │  Only AI tweets saved │
                    └───────────────────────┘
```

## Database Schema
```
┌─────────────────────────────────────────────────────────────────────┐
│                          SUPABASE                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐     │
│  │   sources   │        │   articles  │        │    tweets   │     │
│  ├─────────────┤        ├─────────────┤        ├─────────────┤     │
│  │ id          │◄───────┤ source_id   │        │ source_id   │     │
│  │ name        │        │ headline    │        │ tweet_id    │     │
│  │ url         │        │ url         │        │ content     │     │
│  │ source_type │        │ full_content│        │ author      │     │
│  │ twitter_usr │        │ is_ai_related        │ is_ai_related     │
│  │ active      │        │ published_at│        │ published_at│     │
│  └─────────────┘        │ summary     │        │ summary     │     │
│                         └─────────────┘        └─────────────┘     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Stage Processing Flow
```
┌─────────────────────────────────────────────────────────────────────┐
│                     STAGE 1: COLLECTION                              │
│     Websites: Homepage → Date Filter → GPT → Scrape → Store          │
│     Twitter: Fetch → GPT Filter → Store                              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   STAGE 2: AI VERIFICATION                           │
│     Skip items already marked is_ai_related: true                    │
│     Only process legacy/missed content                               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   STAGE 3: SUMMARIZATION                             │
│     Generate summaries for all AI content                            │
│     Batch process by author (tweets) or individually (articles)      │
└─────────────────────────────────────────────────────────────────────┘
```

## API Call Efficiency
```
OLD APPROACH (Per Source):
━━━━━━━━━━━━━━━━━━━━━━━
Websites:  30 Firecrawl calls → 30 GPT calls → Store all
Twitter:   Store all tweets → 20 GPT calls → Update records

Total: ~50 API calls per source


NEW APPROACH (Per Source):
━━━━━━━━━━━━━━━━━━━━━━━
Websites:  1 Homepage + 3 Articles (Firecrawl) + 1 GPT batch = 5 calls
Twitter:   1 Twitter API + 1 GPT batch = 2 calls

Total: ~7 API calls per source

💰 REDUCTION: 86% fewer API calls!
```

## Data Flow Summary
```
┌──────────────────────────────────────────────────────────────┐
│                    DAILY PIPELINE @ 9AM                       │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  1. Fetch yesterday's content from all sources                │
│     ├── Websites: Scrape → Filter dates → GPT → Scrape full   │
│     └── Twitter: Fetch dated → GPT batch → Store              │
│                                                                │
│  2. All content marked with is_ai_related during Stage 1      │
│                                                                │
│  3. Generate summaries for AI content                         │
│                                                                │
│  4. Frontend displays categorized AI news by day              │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Key Optimizations
```
✅ Python pre-filters dates (free, fast)
✅ GPT batch evaluation (1 call vs many)
✅ Only scrape/store AI content
✅ Mark is_ai_related immediately
✅ Skip redundant Stage 2 processing
✅ 86% reduction in API calls
✅ 60-70% reduction in database writes
```