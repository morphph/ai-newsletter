from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class SourceBase(BaseModel):
    name: str
    url: str
    category: Optional[str] = None
    active: bool = True

class Source(SourceBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SourceResponse(Source):
    article_count: Optional[int] = 0