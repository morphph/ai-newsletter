# 🚀 Deployment Guide for AI News App

This guide will help you deploy your AI News App with automatic news fetching, completely free!

## Architecture Overview

- **Frontend**: Vercel (React app)
- **Backend API**: Render.com or Railway (FastAPI)
- **Database**: Supabase (already set up)
- **Crawler**: GitHub Actions (runs every 30 minutes)

## Prerequisites

- GitHub account
- Vercel account (free)
- Render.com account (free) or Railway account
- Your existing Supabase project

## Step 1: Push to GitHub

First, push your code to GitHub:

```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

## Step 2: Deploy Backend to Render.com

### Option A: Using Render.com (Recommended)

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ai-news-api`
   - **Root Directory**: `backend`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`
5. Add environment variables:
   - `SUPABASE_URL` = your_supabase_url
   - `SUPABASE_KEY` = your_supabase_key
   - `OPENAI_API_KEY` = your_openai_key
   - `FIRECRAWL_API_KEY` = your_firecrawl_key
   - `ALLOWED_ORIGINS` = https://your-app.vercel.app
6. Click "Create Web Service"
7. Copy the URL (e.g., `https://ai-news-api.onrender.com`)

### Option B: Using Railway.app

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Configure:
   - Set root directory to `/backend`
   - Add the same environment variables as above
5. Railway will auto-detect Python and deploy
6. Copy the generated URL

## Step 3: Deploy Frontend to Vercel

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy from frontend directory:
```bash
cd frontend
vercel
```

3. Follow the prompts:
   - Link to existing project? No
   - What's your project name? `ai-news-app`
   - Which directory is your code in? `./`
   - Want to override settings? No

4. Add environment variable in Vercel Dashboard:
   - Go to your project settings
   - Navigate to "Environment Variables"
   - Add: `VITE_API_URL` = `https://ai-news-api.onrender.com/api`
   - Redeploy for changes to take effect

## Step 4: Setup Automatic Crawling with GitHub Actions

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `OPENAI_API_KEY`
   - `FIRECRAWL_API_KEY`

4. Enable GitHub Actions:
   - Go to Actions tab
   - Enable workflows if prompted

5. The crawler will now run automatically every 30 minutes!

## Step 5: Final Configuration

### Update CORS in Backend

After deployment, update the backend environment variable:
- `ALLOWED_ORIGINS` = `https://your-app.vercel.app`

### Test Everything

1. Visit your Vercel URL
2. Check if articles are loading
3. Manually trigger the crawler from GitHub Actions
4. Verify new articles appear

## Monitoring

### Frontend (Vercel)
- Dashboard: https://vercel.com/dashboard
- Analytics included for free

### Backend (Render)
- Dashboard: https://dashboard.render.com
- Logs available in web service dashboard

### Crawler (GitHub Actions)
- Go to Actions tab in your GitHub repo
- View run history and logs

### Database (Supabase)
- Use Supabase dashboard to monitor data
- Check table editor for articles and sources

## Troubleshooting

### Frontend not connecting to backend?
- Check VITE_API_URL environment variable
- Ensure backend is running (check Render dashboard)
- Verify CORS settings in backend

### Crawler not running?
- Check GitHub Actions tab for errors
- Verify secrets are set correctly
- Manually trigger to test

### Backend crashes on Render?
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure requirements.txt is complete

## Cost Summary

- **Vercel**: Free (100GB bandwidth/month)
- **Render**: Free (750 hours/month)
- **GitHub Actions**: Free (2000 minutes/month)
- **Supabase**: Free tier (already using)
- **Total**: $0/month 🎉

## Alternative Deployment Options

### Backend Alternatives
- **Railway.app**: Similar to Render, good free tier
- **Fly.io**: More control, requires credit card
- **Google Cloud Run**: Generous free tier
- **AWS Lambda**: Complex but very scalable

### Crawler Alternatives
- **Vercel Cron Jobs**: Requires Pro plan ($20/month)
- **Render Cron Jobs**: Available on paid plans
- **External cron services**: cron-job.org (free)

## Next Steps

1. Set up custom domain (optional)
2. Add monitoring (UptimeRobot free tier)
3. Implement caching for better performance
4. Add more news sources
5. Create mobile app with React Native

## Support

If you encounter issues:
1. Check the logs in respective dashboards
2. Ensure all environment variables are set
3. Verify your API keys are valid
4. Check rate limits on external APIs

Congratulations! Your AI News App is now live and automatically fetching news! 🚀