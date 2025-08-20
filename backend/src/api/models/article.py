from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class ArticleBase(BaseModel):
    headline: str
    url: str
    summary: Optional[str] = None
    full_content: Optional[str] = None
    is_ai_related: bool = False
    tags: Optional[List[str]] = []
    image_url: Optional[str] = None
    # Twitter-specific fields
    tweet_id: Optional[str] = None
    author_username: Optional[str] = None
    like_count: Optional[int] = 0
    retweet_count: Optional[int] = 0
    reply_count: Optional[int] = 0

class ArticleCreate(ArticleBase):
    source_id: UUID
    published_at: datetime

class ArticleUpdate(BaseModel):
    summary: Optional[str] = None
    full_content: Optional[str] = None
    is_ai_related: Optional[bool] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    # Twitter engagement updates
    like_count: Optional[int] = None
    retweet_count: Optional[int] = None
    reply_count: Optional[int] = None

class Article(ArticleBase):
    id: UUID
    source_id: UUID
    published_at: datetime
    scraped_at: datetime
    view_count: int = 0
    included_in_newsletter: bool = False

    class Config:
        from_attributes = True

class ArticleResponse(Article):
    source_name: Optional[str] = None
    source_category: Optional[str] = None
    source_type: Optional[str] = None