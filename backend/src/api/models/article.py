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

class ArticleCreate(ArticleBase):
    source_id: UUID
    published_at: datetime

class ArticleUpdate(BaseModel):
    summary: Optional[str] = None
    full_content: Optional[str] = None
    is_ai_related: Optional[bool] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None

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