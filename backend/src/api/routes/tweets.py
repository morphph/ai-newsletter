from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime, timedelta
from uuid import UUID

from ..models.tweet import Tweet, TweetResponse, TweetThread, TwitterStats
from ...services.twitter_supabase_service import TwitterSupabaseService

router = APIRouter(prefix="/tweets", tags=["tweets"])
twitter_service = TwitterSupabaseService()

@router.get("/", response_model=List[TweetResponse])
async def get_tweets(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ai_only: bool = Query(False),
    author: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get tweets with optional filtering"""
    try:
        if author:
            tweets = await twitter_service.get_tweets_by_author(author, limit)
        elif start_date and end_date:
            # Get tweets in date range
            tweets = []
            current_date = start_date
            while current_date <= end_date:
                daily_tweets = await twitter_service.get_tweets_by_date(current_date, ai_only)
                tweets.extend(daily_tweets)
                current_date += timedelta(days=1)
            tweets = tweets[offset:offset + limit]
        else:
            # Get recent tweets
            tweets = await twitter_service.get_tweets_by_date(
                date.today() - timedelta(days=1),
                ai_only
            )
            tweets = tweets[offset:offset + limit]
        
        return tweets
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-date/{target_date}", response_model=List[TweetResponse])
async def get_tweets_by_date(
    target_date: date,
    ai_only: bool = Query(False)
):
    """Get tweets for a specific date"""
    try:
        tweets = await twitter_service.get_tweets_by_date(target_date, ai_only)
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-author/{username}", response_model=List[TweetResponse])
async def get_tweets_by_author(
    username: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get tweets by a specific author"""
    try:
        tweets = await twitter_service.get_tweets_by_author(username, limit)
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/thread/{conversation_id}", response_model=TweetThread)
async def get_tweet_thread(conversation_id: str):
    """Get all tweets in a thread"""
    try:
        tweets = await twitter_service.get_tweet_thread(conversation_id)
        
        if not tweets:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Calculate thread statistics
        total_engagement = sum(
            t.get('like_count', 0) + t.get('retweet_count', 0) * 2 
            for t in tweets
        )
        participants = set(t.get('author_username') for t in tweets)
        
        return TweetThread(
            conversation_id=conversation_id,
            tweets=tweets,
            total_engagement=total_engagement,
            participant_count=len(participants)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-engagement", response_model=List[TweetResponse])
async def get_top_tweets_by_engagement(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100)
):
    """Get top tweets by engagement score"""
    try:
        tweets = await twitter_service.get_top_tweets_by_engagement(days, limit)
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[TweetResponse])
async def search_tweets(
    q: str = Query(..., min_length=1),
    ai_only: bool = Query(True)
):
    """Search tweets by content"""
    try:
        tweets = await twitter_service.search_tweets(q, ai_only)
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{username}", response_model=TwitterStats)
async def get_twitter_stats(
    username: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get statistics for a Twitter source"""
    try:
        stats = await twitter_service.get_twitter_stats(username, days)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Twitter source not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unprocessed", response_model=List[Tweet])
async def get_unprocessed_tweets(
    limit: int = Query(100, ge=1, le=500)
):
    """Get tweets that haven't been AI processed yet"""
    try:
        tweets = await twitter_service.get_unprocessed_tweets(limit)
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))