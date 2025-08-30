# Crawler Issues and Fixes

## Current Status
The crawler is working but has two issues that need fixing:

## Issue 1: OpenAI API Parameter Errors ⚠️

**Problem**: The OpenAI API is rejecting some parameters:
- `temperature` parameter doesn't support 0.5 (only default value 1)  
- `max_tokens` parameter should be `max_completion_tokens` instead

**Files to fix**:
- `backend/src/services/openai_service.py`

**Solution**: Update the OpenAI service to use correct parameters for the model.

## Issue 2: Firecrawl API Credits Exhausted 💳

**Problem**: All website scraping is failing with "402 Payment Required - Insufficient credits"

**Solutions**:
1. **Add more credits**: Go to https://firecrawl.dev/pricing and add credits to your account
2. **Use free tier efficiently**: The free tier has limited credits, so you may want to:
   - Reduce frequency of crawls
   - Limit number of sources
   - Only scrape the most important sources

## What IS Working ✅
- Environment variables are correctly configured
- Database connection is working
- Twitter/X fetching is working perfectly
- AI filtering for tweets is working
- Tweet storage in database is successful
- 6 AI-related tweets were successfully collected and stored

## GitHub Actions Setup

To complete the GitHub Actions setup:

1. **Add secrets to GitHub** (if not already done):
   - Go to repository Settings → Secrets and variables → Actions
   - Add: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, FIRECRAWL_API_KEY

2. **Push the fixed workflow file**:
   ```bash
   git add .github/workflows/crawler.yml
   git commit -m "Fix crawler workflow"
   git push
   ```
   Note: You may need a personal access token with 'workflow' scope

3. **Test the workflow**:
   - Go to Actions tab on GitHub
   - Click "AI News Crawler" 
   - Click "Run workflow"
   - Monitor the logs

## Quick Fixes

### Fix OpenAI API issues:
```python
# In backend/src/services/openai_service.py
# Change max_tokens to max_completion_tokens
# Remove temperature parameter or set to 1
```

### Monitor Firecrawl credits:
- Check your usage at: https://app.firecrawl.dev/dashboard
- Consider upgrading plan if needed

## Summary
- **Twitter crawling**: ✅ Working perfectly
- **Website scraping**: ❌ Needs Firecrawl credits
- **AI processing**: ⚠️ Works but needs parameter fixes
- **Database storage**: ✅ Working perfectly