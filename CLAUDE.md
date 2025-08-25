# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI News aggregation system that collects AI/ML news from websites and Twitter, filters relevant content using GPT-4, and provides a web interface for browsing. The system uses a three-tier architecture with React frontend, FastAPI backend, and Supabase database.

## Common Development Commands

### Backend (Python/FastAPI)
```bash
# Start backend API server
cd backend
python run.py

# Run news crawler manually
cd backend
python -m src.workers.news_crawler_v3 --once  # Run once
python -m src.workers.news_crawler_v3 --interval 30  # Run every 30 minutes

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Frontend (React/Vite)
```bash
# Start frontend dev server
cd frontend
npm run dev

# Build frontend for production
cd frontend
npm run build

# Run frontend linting
cd frontend
npm run lint
```

### Testing & Validation
```bash
# No test framework configured yet - check with user before adding tests
# Frontend uses ESLint for linting: npm run lint
```

## Architecture & Key Components

### Data Flow
1. **Content Collection**: `backend/src/workers/news_crawler_v3.py` orchestrates the entire pipeline
   - Fetches sources from database (websites + Twitter accounts)
   - Scrapes websites using Firecrawl API
   - Collects tweets via Twitter API
   
2. **Content Processing**: 
   - Pre-filtering: `backend/src/utils/content_filters.py` applies keyword/pattern matching
   - AI filtering: `backend/src/services/openai_service.py` uses GPT-4 to identify AI/ML content
   - Summaries generated for relevant content

3. **Storage**: Supabase database with separated tables
   - `sources`: All content sources (websites and Twitter accounts)
   - `articles`: Website articles
   - `tweets`: Twitter/X posts
   - Unified through `source_id` foreign key

### API Structure
- **Main app**: `backend/src/api/main.py` - FastAPI application setup
- **Routes**: `backend/src/api/routes/`
  - `articles.py`: Article CRUD operations
  - `tweets.py`: Tweet operations
  - `content.py`: Unified content endpoint
  - `sources.py`: Source management
  - `monitoring.py`: System health checks

### Service Layer (`backend/src/services/`)
- `supabase_client.py`: Database operations for articles
- `twitter_supabase_service.py`: Database operations for tweets
- `firecrawl_service.py`: Web scraping via Firecrawl API
- `openai_service.py`: GPT-4 integration for filtering/summarization
- `twitter_service.py`: Twitter API integration

### Frontend Structure
- React + Vite setup with Tailwind CSS
- State management via Zustand
- API calls through Axios
- React Query for data fetching

## Environment Setup

Required environment variables (copy `.env.example` to `.env`):
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key  
- `FIRECRAWL_API_KEY`: For web scraping
- `OPENAI_API_KEY`: For AI filtering/summarization
- `TWITTER_BEARER_TOKEN`: (Optional) For Twitter API access

## Database Schema

Key tables and relationships:
- **sources**: Central source registry with `source_type` field ('website' or 'twitter')
- **articles**: Website content with full_content, summaries, AI relevance flags
- **tweets**: Twitter posts with engagement metrics
- Both content tables link to sources via `source_id`

Schema files:
- `database_schema.json`: Current schema structure
- `database_schema_documentation.md`: Detailed documentation

## Deployment Configuration

- **Frontend**: Vercel deployment via `vercel.json`
- **Backend**: Render.com deployment via `backend/render.yaml`
- **Crawler**: GitHub Actions scheduled job (`.github/workflows/crawler.yml`)

## Important Notes

- CORS is configured to allow all origins in development
- The crawler runs as `news_crawler_v3.py` (latest version)
- Twitter integration requires bearer token for API v2
- Pre-filtering happens before expensive AI calls to reduce costs
- Processing stages tracked for debugging failed enrichments