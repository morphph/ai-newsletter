# AI News App

An automated AI news aggregation system that scrapes AI/ML news from multiple sources, filters relevant content, and generates summaries.

## Features

- **Automated Web Scraping**: Uses Firecrawl to scrape content from AI news sources
- **AI-Powered Filtering**: GPT-4o identifies AI/ML-related articles from scraped content
- **Smart Summarization**: Generates 2-3 sentence summaries for each article
- **Database Storage**: Stores articles in Supabase
- **Web Interface**: Frontend app for browsing AI news
- **API Access**: RESTful API for retrieving articles

## Prerequisites

- Python 3.8+
- Supabase account and project
- Firecrawl API key
- OpenAI API key

## Installation

1. Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

3. Set up your Supabase database using the schema in `database_schema.sql`

4. Seed initial news sources:
```bash
python scripts/seed_sources.py
```

## Configuration

### Environment Variables

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `FIRECRAWL_API_KEY`: Your Firecrawl API key
- `OPENAI_API_KEY`: Your OpenAI API key


## Usage

### Start the Backend API
```bash
cd backend
python run.py
```

### Start the Frontend
```bash
cd frontend
npm run dev
```

### Run the News Crawler
```bash
cd backend
python -m src.workers.news_crawler --once  # Run once
python -m src.workers.news_crawler --interval 30  # Run every 30 minutes
```

## Workflow

1. **Fetch Sources**: Retrieves active news sources from database
2. **Scrape Homepages**: Uses Firecrawl to get markdown content from each source
3. **Filter Articles**: GPT-4o extracts AI/ML-related articles
4. **Store Articles**: Saves new articles to database
5. **Enrich Content**: Fetches full article content and generates summaries
6. **Display Articles**: Shows articles in web interface with filters

## Deployment

The app is configured for free, automatic deployment:

- **Frontend**: Deploy to Vercel (free)
- **Backend**: Deploy to Render.com (free tier)
- **Crawler**: Runs on GitHub Actions (free, every 30 minutes)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## Project Structure

```
├── backend/
│   ├── src/
│   │   ├── api/                  # FastAPI application
│   │   ├── services/             # Core services
│   │   └── workers/              # Background workers
│   └── run.py                    # Backend entry point
├── frontend/
│   ├── src/                      # React application
│   └── package.json              # Frontend dependencies
├── src/
│   └── services/                 # Shared services
├── scripts/
│   └── manage_sources.py         # Source management
├── .github/
│   └── workflows/                # GitHub Actions for crawler
├── database_schema_current.sql   # Current database schema
└── requirements.txt               # Python dependencies
```

## Adding New Sources

To add new news sources, you can either:

1. Add them to `scripts/seed_sources.py` and run it again
2. Insert directly into the `sources` table in Supabase

## Monitoring

The system logs detailed information about:
- Source processing status
- Article discovery and filtering
- Summary generation
- Newsletter creation
- Email sending (if configured)

## Error Handling

- Failed source scraping continues with next source
- Failed article enrichment doesn't block newsletter generation
- Email failures are logged but don't stop the workflow