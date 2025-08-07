# Manual GitHub Actions Update Required

Due to GitHub security restrictions, the workflow file cannot be updated via API. Please manually update the following:

## File: `.github/workflows/crawler.yml`

### Change Line 5:
```yaml
# FROM:
    - cron: '*/30 * * * *'

# TO:
    - cron: '0 9 * * *'
```

### Change Line 26:
```yaml
# FROM:
          python -m src.workers.news_crawler --once

# TO:
          # Use the enhanced crawler with three-stage pipeline
          python -m src.workers.news_crawler_v2 --stage all
```

## Complete Updated File:
```yaml
name: AI News Crawler
on:
  workflow_dispatch:
  schedule:
    # Run daily at 9 AM UTC (adjust for your timezone)
    - cron: '0 9 * * *'
jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install and run
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
        run: |
          cd backend
          pip install supabase openai python-dotenv aiohttp python-dateutil beautifulsoup4 lxml
          pip install fastapi uvicorn pydantic pydantic-settings
          pip install firecrawl-py || echo "Firecrawl failed"
          # Use the enhanced crawler with three-stage pipeline
          python -m src.workers.news_crawler_v2 --stage all
```

## How to Update:
1. Go to your GitHub repository
2. Navigate to `.github/workflows/crawler.yml`
3. Click "Edit" (pencil icon)
4. Replace the content with the updated version above
5. Commit directly to main branch

This change will:
- Run the crawler once daily at 9 AM UTC instead of every 30 minutes
- Use the new three-stage pipeline crawler
- Significantly reduce API usage and costs