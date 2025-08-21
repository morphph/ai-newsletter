from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from pydantic import BaseModel

from ...services.supabase_client import SupabaseService

router = APIRouter(prefix="/content", tags=["unified-content"])
supabase_service = SupabaseService()

class UnifiedContentItem(BaseModel):
    content_type: str
    id: str
    source_name: str
    source_type: str
    headline: str
    url: str
    content: Optional[str]
    summary: Optional[str]
    is_ai_related: bool
    tags: Optional[List[str]]
    published_at: datetime
    fetched_at: datetime
    engagement_score: int
    like_count: int
    retweet_count: int
    reply_count: int
    view_count: int
    included_in_newsletter: bool
    image_url: Optional[str]
    author_username: Optional[str]
    tweet_id: Optional[str]

@router.get("/unified", response_model=List[UnifiedContentItem])
async def get_unified_content(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ai_only: bool = Query(False),
    content_type: Optional[str] = Query(None, regex="^(article|tweet)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    sort_by: str = Query("published_at", regex="^(published_at|engagement_score)$")
):
    """
    Get unified content from both articles and tweets
    
    - **content_type**: Filter by content type (article or tweet)
    - **ai_only**: Only return AI-related content
    - **start_date/end_date**: Filter by date range
    - **sort_by**: Sort by published_at or engagement_score
    """
    try:
        # Build query for unified_content view
        query = supabase_service.client.table('unified_content').select('*')
        
        # Apply filters
        if ai_only:
            query = query.eq('is_ai_related', True)
        
        if content_type:
            query = query.eq('content_type', content_type)
        
        if start_date:
            query = query.gte('published_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('published_at', end_date.isoformat())
        
        # Apply sorting
        if sort_by == 'engagement_score':
            query = query.order('engagement_score', desc=True)
        else:
            query = query.order('published_at', desc=True)
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        response = query.execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feed/today", response_model=List[UnifiedContentItem])
async def get_todays_feed(
    ai_only: bool = Query(True)
):
    """Get today's content feed combining articles and tweets"""
    try:
        today = date.today()
        
        # Use date range for filtering
        from datetime import time
        start_of_day = datetime.combine(today, time.min).isoformat()
        end_of_day = datetime.combine(today, time.max).isoformat()
        
        query = supabase_service.client.table('unified_content').select('*').gte(
            'published_at', start_of_day
        ).lte(
            'published_at', end_of_day
        )
        
        if ai_only:
            query = query.eq('is_ai_related', True)
        
        query = query.order('engagement_score', desc=True).order('published_at', desc=True)
        
        response = query.execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feed/trending", response_model=List[UnifiedContentItem])
async def get_trending_content(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100)
):
    """Get trending content based on engagement"""
    try:
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        query = supabase_service.client.table('unified_content').select('*').gte(
            'published_at', start_date
        ).eq(
            'is_ai_related', True
        ).order(
            'engagement_score', desc=True
        ).limit(limit)
        
        response = query.execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/daily")
async def get_daily_content_stats(
    days: int = Query(7, ge=1, le=30)
):
    """Get daily statistics for content"""
    try:
        stats = []
        
        for i in range(days):
            target_date = date.today() - timedelta(days=i)
            
            # Get counts for the day
            articles_query = supabase_service.client.table('articles').select(
                'id', count='exact'
            ).eq('published_at', target_date.isoformat())
            
            tweets_query = supabase_service.client.table('tweets').select(
                'id', count='exact'
            ).eq('published_at::date', target_date.isoformat())
            
            articles_response = articles_query.execute()
            tweets_response = tweets_query.execute()
            
            # Get AI counts
            ai_articles_query = supabase_service.client.table('articles').select(
                'id', count='exact'
            ).eq('published_at', target_date.isoformat()).eq('is_ai_related', True)
            
            ai_tweets_query = supabase_service.client.table('tweets').select(
                'id', count='exact'
            ).eq('published_at::date', target_date.isoformat()).eq('is_ai_related', True)
            
            ai_articles_response = ai_articles_query.execute()
            ai_tweets_response = ai_tweets_query.execute()
            
            stats.append({
                'date': target_date.isoformat(),
                'total_articles': articles_response.count or 0,
                'total_tweets': tweets_response.count or 0,
                'ai_articles': ai_articles_response.count or 0,
                'ai_tweets': ai_tweets_response.count or 0,
                'total_content': (articles_response.count or 0) + (tweets_response.count or 0),
                'total_ai_content': (ai_articles_response.count or 0) + (ai_tweets_response.count or 0)
            })
        
        return {
            'period_days': days,
            'daily_stats': stats,
            'summary': {
                'total_content': sum(s['total_content'] for s in stats),
                'total_ai_content': sum(s['total_ai_content'] for s in stats),
                'avg_daily_content': sum(s['total_content'] for s in stats) / days,
                'avg_daily_ai_content': sum(s['total_ai_content'] for s in stats) / days
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/newsletter/candidates", response_model=List[UnifiedContentItem])
async def get_newsletter_candidates(
    target_date: Optional[date] = Query(None),
    min_engagement: int = Query(0)
):
    """Get content candidates for newsletter"""
    try:
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        query = supabase_service.client.table('unified_content').select('*').eq(
            'published_at::date', target_date.isoformat()
        ).eq(
            'is_ai_related', True
        ).eq(
            'included_in_newsletter', False
        ).gte(
            'engagement_score', min_engagement
        ).order(
            'engagement_score', desc=True
        ).limit(50)
        
        response = query.execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))