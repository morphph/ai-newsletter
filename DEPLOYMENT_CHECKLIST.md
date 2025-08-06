# 📋 Deployment Checklist

## Pre-Deployment
- [ ] All code committed to GitHub
- [ ] Environment variables documented
- [ ] Test locally one more time
- [ ] Remove any sensitive data from code

## Backend Deployment (Render.com)
- [ ] Create Render account
- [ ] Connect GitHub repository
- [ ] Set root directory to `/backend`
- [ ] Add environment variables:
  - [ ] SUPABASE_URL
  - [ ] SUPABASE_KEY
  - [ ] OPENAI_API_KEY
  - [ ] FIRECRAWL_API_KEY
  - [ ] ALLOWED_ORIGINS (add after frontend deploys)
- [ ] Deploy and get URL
- [ ] Test health endpoint: `https://your-api.onrender.com/health`

## Frontend Deployment (Vercel)
- [ ] Install Vercel CLI: `npm i -g vercel`
- [ ] Run `vercel` in `/frontend` directory
- [ ] Add environment variable in Vercel dashboard:
  - [ ] VITE_API_URL = Backend URL + `/api`
- [ ] Redeploy after adding env var
- [ ] Test frontend URL

## Crawler Setup (GitHub Actions)
- [ ] Add GitHub Secrets:
  - [ ] SUPABASE_URL
  - [ ] SUPABASE_KEY
  - [ ] OPENAI_API_KEY
  - [ ] FIRECRAWL_API_KEY
- [ ] Enable GitHub Actions
- [ ] Manually trigger first run
- [ ] Verify crawler completes successfully

## Post-Deployment
- [ ] Update backend ALLOWED_ORIGINS with Vercel URL
- [ ] Test article fetching on frontend
- [ ] Verify crawler runs on schedule
- [ ] Monitor for 24 hours
- [ ] Set up error notifications (optional)

## URLs to Save
- Frontend URL: ___________________________
- Backend URL: ___________________________
- GitHub Repo: ___________________________
- Render Dashboard: ___________________________
- Vercel Dashboard: ___________________________