# AI Newsletter Project Plan

---

## Table of Contents
1. [Feature Overview](#feature-overview)
2. [Data Flow](#data-flow)
3. [Step-by-Step Process](#step-by-step-process)
4. [Code Example: Firecrawl](#code-example-firecrawl)
5. [Initial Source List](#initial-source-list)

---

## Feature Overview
An AI newsletter that features updates from targeted websites.

---

## Data Flow

```
Cron (2AM)
   ↓
Fetch source URLs from Supabase
   ↓
Firecrawl scrapes source URLs
   ↓
GPT-4o filters for today's AI/LLM stories
   ↓
Firecrawl fetches each article URL
   ↓
GPT-4o summarizes full content
   ↓
Newsletter with rich summaries
```

---

## Step-by-Step Process

1. **Homepage Scrape**
    - **Input:** https://www.anthropic.com/news
    - **Output:** Markdown with multiple article headlines/links

2. **AI Filtering**
    - GPT-4o extracts today's AI/LLM-related stories
    - **Returns:** Array of `{headline, link, date}`

3. **Full Article Fetch (NEW)**
    - For each story link, Firecrawl scrapes the full article
    - GPT-4o creates 2-3 sentence summary
    - **Returns:** `{headline, link, date, fullContent, summary}`

4. **Newsletter Generation**
    - Uses full content/summaries for better newsletter quality
    - Selects top 10 stories with context

---

## Code Example: Firecrawl

> **Install with:**
> 
> `pip install firecrawl-py`

```python
import asyncio
from firecrawl import AsyncFirecrawlApp

async def main():
    app = AsyncFirecrawlApp(api_key='YOUR_FIRECRAWL_API_KEY')
    response = await app.scrape_url(
        url='https://www.anthropic.com/news',
        formats=['markdown'],
        only_main_content=True,
        parse_pdf=True,
        max_age=14400000
    )
    print(response)

asyncio.run(main())
```

---

## Initial Source List

#### Official AI Companies
- [OpenAI News](https://openai.com/news/)
- [Anthropic News](https://www.anthropic.com/news)
- [Anthropic Release Notes](https://docs.anthropic.com/en/release-notes/overview)
- [Anthropic Research](https://www.anthropic.com/research)
- [Google AI Blog](https://blog.google/technology/ai/)
- [Google Developers Blog](https://blog.google/technology/developers/)
- [Google DeepMind Blog](https://blog.google/technology/google-deepmind/)
- [Google Gemini Developer Blog](https://developers.googleblog.com/en/search/?product_categories=Gemini)

#### AI Researchers & Thought Leaders
- [Hacker News](https://news.ycombinator.com/)
- [Reuters AI News](https://www.reuters.com/technology/artificial-intelligence/)
- [Simon Willison](https://simonwillison.net/)

#### AI Tools
- [Firecrawl Blog](https://www.firecrawl.dev/blog/)