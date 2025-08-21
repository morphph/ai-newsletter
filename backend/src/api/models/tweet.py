from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class TweetBase(BaseModel):
    tweet_id: str
    author_username: str
    content: str
    
    # Engagement metrics
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    view_count: int = 0
    bookmark_count: int = 0
    
    # Tweet metadata
    is_reply: bool = False
    is_retweet: bool = False
    is_quote_tweet: bool = False
    has_media: bool = False
    media_urls: Optional[List[str]] = []
    hashtags: Optional[List[str]] = []
    mentions: Optional[List[str]] = []
    urls: Optional[List[str]] = []
    
    # Thread information
    conversation_id: Optional[str] = None
    in_reply_to_tweet_id: Optional[str] = None
    quoted_tweet_id: Optional[str] = None
    thread_position: Optional[int] = None
    
    # Quoted tweet content
    quoted_tweet_content: Optional[str] = None
    quoted_tweet_author: Optional[str] = None
    
    # AI processing
    is_ai_related: bool = False
    ai_summary: Optional[str] = None
    ai_tags: Optional[List[str]] = []
    ai_relevance_score: Optional[float] = None

class TweetCreate(TweetBase):
    source_id: UUID
    published_at: datetime

class TweetUpdate(BaseModel):
    # Engagement updates (can change over time)
    like_count: Optional[int] = None
    retweet_count: Optional[int] = None
    reply_count: Optional[int] = None
    view_count: Optional[int] = None
    bookmark_count: Optional[int] = None
    
    # AI processing updates
    is_ai_related: Optional[bool] = None
    ai_summary: Optional[str] = None
    ai_tags: Optional[List[str]] = None
    ai_relevance_score: Optional[float] = None
    
    # Newsletter tracking
    included_in_newsletter: Optional[bool] = None
    display_priority: Optional[int] = None

class Tweet(TweetBase):
    id: UUID
    source_id: UUID
    published_at: datetime
    fetched_at: datetime
    updated_at: Optional[datetime] = None
    included_in_newsletter: bool = False
    newsletter_date: Optional[datetime] = None
    display_priority: int = 0
    
    class Config:
        from_attributes = True

class TweetResponse(Tweet):
    source_name: Optional[str] = None
    engagement_score: Optional[int] = None
    
    @property
    def calculated_engagement_score(self) -> int:
        """Calculate engagement score based on metrics"""
        return self.like_count + (self.retweet_count * 2) + self.reply_count

class TweetThread(BaseModel):
    conversation_id: str
    tweets: List[Tweet]
    total_engagement: int
    participant_count: int
    
class TwitterStats(BaseModel):
    date: datetime
    source_name: str
    twitter_username: str
    tweet_count: int
    ai_tweet_count: int
    avg_likes: float
    avg_retweets: float
    max_likes: int
    max_retweets: int
    total_engagement: int