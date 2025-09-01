# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI News Application - A full-stack web application that aggregates and curates AI-related news from various sources including websites and Twitter/X. The application consists of a React frontend and FastAPI backend with automated news crawling via GitHub Actions.

## Architecture

### Backend (Python/FastAPI)
- **API Server**: FastAPI application in `backend/src/api/main.py`
- **Services**: Located in `backend/src/services/`
  - `supabase_client.py`: Database operations
  - `twitter_supabase_service.py`: Twitter data management
  - `firecrawl_service.py`: Web scraping service
  - `openai_service.py`: AI content analysis
  - `twitter_service.py`: Twitter/X API integration
- **Workers**: Background tasks in `backend/src/workers/`
  - `news_crawler_v3.py`: Main news aggregation worker
- **Routes**: API endpoints in `backend/src/api/routes/`
  - Articles, sources, monitoring, tweets, content endpoints

### Frontend (React/Vite)
- **Framework**: React 18 with Vite bundler
- **Styling**: Tailwind CSS
- **State Management**: React Query + Zustand
- **Routing**: React Router v6
- **Main Components**: Located in `frontend/src/components/`
- **Pages**: Located in `frontend/src/pages/`
- **API Services**: Located in `frontend/src/services/`

### Database
- **Provider**: Supabase (PostgreSQL)
- **Main Tables**: articles, tweets, sources, tweet_sources
- **Migrations**: Located in `backend/migrations/`

## Common Development Commands

### Frontend Development
```bash
cd frontend
npm install              # Install dependencies
npm run dev              # Start development server (Vite)
npm run build            # Build for production
npm run lint             # Run ESLint
npm run preview          # Preview production build
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt    # Install Python dependencies
python run.py                       # Start FastAPI server (port 8000)
uvicorn src.api.main:app --reload  # Alternative with auto-reload
```

### Testing & Verification
```bash
# Backend API testing
curl http://localhost:8000/health
curl http://localhost:8000/api/articles

# Frontend linting
cd frontend && npm run lint

# Run news crawler manually
cd backend && python src/workers/news_crawler_v3.py --once
```

### Deployment & CI/CD
- **Frontend**: Deployed on Vercel (uses `build.sh` script)
- **Backend**: Deployed on Render (configured in `render.yaml`)
- **GitHub Actions**: Automated news crawling every 6 hours (`news_crawler.yml`)
  - Manual trigger available via workflow_dispatch

## Environment Variables

### Backend (.env)
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
FIRECRAWL_API_KEY=your_firecrawl_key
TWITTER_API_KEY=your_twitter_key
PORT=8000
```

### Frontend
- API endpoint configured in service files
- Default backend URL: http://localhost:8000

## Project Structure

```
/
├── frontend/              # React application
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/       # Route pages
│   │   ├── services/    # API clients
│   │   └── hooks/       # Custom React hooks
│   └── package.json
├── backend/              # FastAPI application
│   ├── src/
│   │   ├── api/         # API routes and middleware
│   │   ├── services/    # Business logic services
│   │   ├── utils/       # Utility functions
│   │   └── workers/     # Background tasks
│   ├── requirements.txt
│   └── run.py
├── .github/workflows/    # GitHub Actions
└── docs/                # Documentation
```

## Key Features & Workflows

1. **News Aggregation**: Automated crawler fetches articles and tweets from configured sources
2. **AI Filtering**: OpenAI API analyzes content for AI relevance
3. **Content Storage**: Separate storage for tweets (tweets table) and articles (articles table)
4. **API Endpoints**: RESTful API serves content to frontend
5. **Real-time Updates**: Frontend polls for new content periodically

## Data Flow

1. GitHub Actions triggers `news_crawler_v3.py` every 6 hours
2. Crawler fetches content from configured sources
3. Content is filtered and analyzed for AI relevance
4. Processed content stored in Supabase
5. Frontend fetches and displays content via API

## Important Considerations

- CORS is configured to allow all origins in development
- Background workers use async operations for efficiency
- Content deduplication based on URL/tweet ID
- Date-based filtering for relevant content
- Automatic retry logic for failed API calls