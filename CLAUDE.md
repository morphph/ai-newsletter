# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI News Aggregator - An automated system that collects, filters, and summarizes AI/ML news from multiple sources including websites and Twitter/X.

## Architecture

### Data Flow
1. **Sources**: Website URLs and Twitter handles stored in `sources` table
2. **Collection**: 
   - Website articles scraped via Firecrawl API → stored in `articles` table
   - Tweets fetched via Twitter API → stored in `tweets` table
3. **Processing**: GPT-4o filters AI-related content and generates summaries
4. **Access**: Unified content view combines both tables for backward compatibility

### Key Services
- **Supabase**: Database (PostgreSQL)
- **Firecrawl**: Web scraping API
- **OpenAI**: Content filtering and summarization
- **Twitter API**: Tweet collection

## Commands

### Backend Development
```bash
cd backend
python run.py                                    # Start FastAPI server (port 8000)
python -m src.workers.news_crawler_v3 --once    # Run crawler once
python -m src.workers.news_crawler_v3 --interval 30  # Run every 30 minutes
```

### Frontend Development
```bash
cd frontend
npm install                # Install dependencies
npm run dev               # Start dev server (Vite)
npm run build            # Build for production
npm run lint             # Run ESLint
```

### Source Management
```bash
python scripts/manage_sources.py                # Manage website sources
python scripts/manage_twitter_sources.py        # Manage Twitter sources
python backend/list_sources.py                  # List all sources with stats
```

## Database Schema

### Core Tables
- `sources`: All content sources (websites and Twitter accounts)
  - `source_type`: 'website' or 'twitter'
  - `twitter_username`: For Twitter sources only
  
- `articles`: Website articles
  - Links to `sources` via `source_id`
  - `processing_stage`: Pipeline tracking
  
- `tweets`: Twitter content
  - Links to `sources` via `source_id`
  - Engagement metrics included

- `unified_content`: View combining articles and tweets

## API Structure

Backend API (FastAPI) at `/api`:
- `/articles/*` - Article endpoints
- `/tweets/*` - Tweet endpoints  
- `/content/unified` - Unified content access
- `/sources/*` - Source management
- `/monitoring/*` - System monitoring

## Environment Variables

Required in `.env`:
```
SUPABASE_URL=
SUPABASE_KEY=
OPENAI_API_KEY=
FIRECRAWL_API_KEY=
```

Frontend needs:
```
VITE_API_URL=http://localhost:8000/api  # Or production URL
```

## Deployment

- **Frontend**: Vercel (automatic from main branch)
- **Backend**: Render.com (configured in render.yaml)
- **Crawler**: GitHub Actions (runs daily at 9 AM UTC)

## Key Implementation Details

### Content Filtering
The system uses a hybrid approach:
1. Pre-filtering with keywords (ContentFilter class)
2. AI validation with GPT-4o for accuracy
3. Processing stages tracked in database

### Twitter Integration
- Separate `tweets` table for Twitter-specific fields
- `TwitterService` handles API interactions
- `TwitterSupabaseService` manages database operations

### Error Handling
- Failed sources don't block other processing
- Retry logic with exponential backoff
- Detailed logging throughout pipeline

## Testing Approach

No formal test framework is configured. To test:
1. Run crawler with `--once` flag for single execution
2. Check database tables for new content
3. Monitor API endpoints via `/api/monitoring/status`
4. View logs for detailed processing information