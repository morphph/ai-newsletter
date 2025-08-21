"""
Twitter-specific Supabase service for managing tweets in the database
"""

import os
from typing import List, Dict, Optional
from datetime import datetime, date, time
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class TwitterSupabaseService:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.client: Client = create_client(url, key)
    
    async def insert_tweet(self, tweet_data: Dict) -> Dict:
        """Insert a new tweet into the tweets table"""
        try:
            # Check if tweet already exists
            existing = self.client.table('tweets').select('id').eq('tweet_id', tweet_data['tweet_id']).execute()
            
            if existing.data and len(existing.data) > 0:
                logger.info(f"Tweet {tweet_data['tweet_id']} already exists, updating engagement metrics")
                # Update engagement metrics if tweet exists
                return await self.update_tweet_engagement(tweet_data['tweet_id'], tweet_data)
            
            # Insert new tweet
            response = self.client.table('tweets').insert(tweet_data).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error inserting tweet: {str(e)}")
            return None
    
    async def update_tweet_engagement(self, tweet_id: str, engagement_data: Dict) -> Dict:
        """Update engagement metrics for an existing tweet"""
        try:
            update_data = {
                'like_count': engagement_data.get('like_count', 0),
                'retweet_count': engagement_data.get('retweet_count', 0),
                'reply_count': engagement_data.get('reply_count', 0),
                'view_count': engagement_data.get('view_count', 0)
            }
            
            response = self.client.table('tweets').update(update_data).eq('tweet_id', tweet_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error updating tweet engagement: {str(e)}")
            return None
    
    async def get_tweets_by_date(self, target_date: date, ai_only: bool = False) -> List[Dict]:
        """Get tweets for a specific date"""
        # Use date range for filtering
        start_of_day = datetime.combine(target_date, time.min).isoformat()
        end_of_day = datetime.combine(target_date, time.max).isoformat()
        
        query = self.client.table('tweets').select('*, sources(name, twitter_username)').gte(
            'published_at', start_of_day
        ).lte(
            'published_at', end_of_day
        )
        
        if ai_only:
            query = query.eq('is_ai_related', True)
        
        response = query.order('like_count', desc=True).execute()
        return response.data
    
    async def get_tweets_by_author(self, username: str, limit: int = 50) -> List[Dict]:
        """Get tweets by a specific author"""
        response = self.client.table('tweets').select('*').eq(
            'author_username', username
        ).order('published_at', desc=True).limit(limit).execute()
        
        return response.data
    
    async def get_tweet_thread(self, conversation_id: str) -> List[Dict]:
        """Get all tweets in a thread/conversation"""
        response = self.client.table('tweets').select('*').eq(
            'conversation_id', conversation_id
        ).order('thread_position').order('published_at').execute()
        
        return response.data
    
    async def mark_tweet_ai_processed(self, tweet_id: str, ai_data: Dict) -> Dict:
        """Mark a tweet as AI processed with summary and tags"""
        try:
            update_data = {
                'is_ai_related': ai_data.get('is_ai_related', False),
                'ai_summary': ai_data.get('summary'),
                'ai_tags': ai_data.get('tags', []),
                'ai_relevance_score': ai_data.get('relevance_score'),
                'ai_processed_at': datetime.now().isoformat()
            }
            
            response = self.client.table('tweets').update(update_data).eq('tweet_id', tweet_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error marking tweet as AI processed: {str(e)}")
            return None
    
    async def get_unprocessed_tweets(self, limit: int = 100) -> List[Dict]:
        """Get tweets that haven't been AI processed yet"""
        response = self.client.table('tweets').select('*').is_('ai_processed_at', 'null').limit(limit).execute()
        return response.data
    
    async def get_top_tweets_by_engagement(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """Get top tweets by engagement score"""
        from datetime import timedelta
        
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        response = self.client.table('tweets').select(
            '*, sources(name, twitter_username)'
        ).gte('published_at', start_date).order(
            'like_count', desc=True
        ).limit(limit).execute()
        
        return response.data
    
    async def search_tweets(self, query: str, ai_only: bool = True) -> List[Dict]:
        """Search tweets by content"""
        search_query = self.client.table('tweets').select('*, sources(name)').ilike('content', f'%{query}%')
        
        if ai_only:
            search_query = search_query.eq('is_ai_related', True)
        
        response = search_query.order('published_at', desc=True).limit(50).execute()
        return response.data
    
    async def get_twitter_stats(self, username: str, days: int = 30) -> Dict:
        """Get statistics for a Twitter source"""
        from datetime import timedelta
        
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        # Get source ID
        source_response = self.client.table('sources').select('id').eq('twitter_username', username).execute()
        
        if not source_response.data:
            return None
        
        source_id = source_response.data[0]['id']
        
        # Get tweet stats
        tweets_response = self.client.table('tweets').select('*').eq(
            'source_id', source_id
        ).gte('published_at', start_date).execute()
        
        tweets = tweets_response.data if tweets_response.data else []
        
        if not tweets:
            return {
                'username': username,
                'period_days': days,
                'total_tweets': 0,
                'ai_tweets': 0,
                'avg_likes': 0,
                'avg_retweets': 0,
                'total_engagement': 0
            }
        
        ai_tweets = [t for t in tweets if t.get('is_ai_related', False)]
        total_likes = sum(t.get('like_count', 0) for t in tweets)
        total_retweets = sum(t.get('retweet_count', 0) for t in tweets)
        
        return {
            'username': username,
            'period_days': days,
            'total_tweets': len(tweets),
            'ai_tweets': len(ai_tweets),
            'avg_likes': total_likes / len(tweets) if tweets else 0,
            'avg_retweets': total_retweets / len(tweets) if tweets else 0,
            'total_engagement': total_likes + (total_retweets * 2),
            'top_tweet': max(tweets, key=lambda t: t.get('like_count', 0)) if tweets else None
        }
    
    async def bulk_insert_tweets(self, tweets: List[Dict]) -> int:
        """Bulk insert multiple tweets"""
        if not tweets:
            return 0
        
        try:
            # Filter out existing tweets
            tweet_ids = [t['tweet_id'] for t in tweets]
            existing_response = self.client.table('tweets').select('tweet_id').in_('tweet_id', tweet_ids).execute()
            existing_ids = {t['tweet_id'] for t in existing_response.data} if existing_response.data else set()
            
            new_tweets = [t for t in tweets if t['tweet_id'] not in existing_ids]
            
            if new_tweets:
                response = self.client.table('tweets').insert(new_tweets).execute()
                return len(response.data) if response.data else 0
            
            return 0
            
        except Exception as e:
            logger.error(f"Error bulk inserting tweets: {str(e)}")
            return 0