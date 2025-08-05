# AI Newsletter Automation

An automated AI newsletter system that scrapes AI/ML news from multiple sources, filters relevant content, generates summaries, and creates a daily newsletter.

## Features

- **Automated Web Scraping**: Uses Firecrawl to scrape content from AI news sources
- **AI-Powered Filtering**: GPT-4o identifies AI/ML-related articles from scraped content
- **Smart Summarization**: Generates 2-3 sentence summaries for each article
- **Newsletter Generation**: Creates professionally formatted newsletters with top stories
- **Database Storage**: Stores articles and newsletters in Supabase
- **Email Distribution**: Optional email sending to subscribers
- **Scheduled Execution**: Runs daily at 2 AM automatically

## Prerequisites

- Python 3.8+
- Supabase account and project
- Firecrawl API key
- OpenAI API key
- (Optional) SMTP credentials for email sending

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

### Optional Email Configuration

- `SMTP_HOST`: SMTP server host (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP server port (default: 587)
- `SMTP_USER`: SMTP username
- `SMTP_PASSWORD`: SMTP password
- `FROM_EMAIL`: Sender email address
- `FROM_NAME`: Sender name (default: AI Newsletter)

## Usage

### Run Once (Manual)
```bash
python main.py --run-now
```

### Run Scheduled (Daily at 2 AM)
```bash
python main.py
```

## Workflow

1. **Fetch Sources**: Retrieves active news sources from database
2. **Scrape Homepages**: Uses Firecrawl to get markdown content from each source
3. **Filter Articles**: GPT-4o extracts AI/ML-related articles published today
4. **Store Articles**: Saves new articles to database
5. **Enrich Content**: Fetches full article content and generates summaries
6. **Generate Newsletter**: Creates newsletter from top 10 articles
7. **Send Emails**: Optionally sends newsletter to subscribers

## Project Structure

```
├── src/
│   ├── services/
│   │   ├── supabase_client.py    # Database operations
│   │   ├── firecrawl_service.py  # Web scraping
│   │   └── openai_service.py     # AI filtering & summarization
│   ├── workflows/
│   │   └── newsletter_workflow.py # Main orchestration logic
│   └── utils/
│       └── email_sender.py        # Email distribution
├── scripts/
│   └── seed_sources.py            # Initialize news sources
├── main.py                        # Entry point & scheduler
├── database_schema.sql            # Supabase schema
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