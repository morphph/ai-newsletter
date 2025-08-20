from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from enum import Enum

class SourceType(str, Enum):
    WEBSITE = "website"
    TWITTER = "twitter"

class SourceBase(BaseModel):
    name: str
    url: str
    source_type: SourceType = SourceType.WEBSITE
    category: Optional[str] = None
    twitter_username: Optional[str] = None
    active: bool = True
    
    @validator('twitter_username')
    def validate_twitter_username(cls, v, values):
        if values.get('source_type') == SourceType.TWITTER and not v:
            raise ValueError('Twitter username is required for Twitter sources')
        if v and v.startswith('@'):
            # Remove @ if provided
            return v[1:]
        return v
    
    @validator('url')
    def validate_url(cls, v, values):
        source_type = values.get('source_type')
        if source_type == SourceType.TWITTER:
            # For Twitter sources, generate URL from username if not provided
            username = values.get('twitter_username')
            if username and not v:
                return f"https://twitter.com/{username}"
        return v

class Source(SourceBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SourceResponse(Source):
    article_count: Optional[int] = 0
    
class SourceCreate(BaseModel):
    name: str
    source_type: SourceType
    url: Optional[str] = None
    category: Optional[str] = None
    twitter_username: Optional[str] = None
    twitter_input: Optional[str] = None  # Accept URL or handle
    active: bool = True
    
    @validator('twitter_username', always=True)
    def validate_twitter_username_create(cls, v, values):
        # If twitter_input is provided, extract username from it
        if values.get('source_type') == SourceType.TWITTER:
            if values.get('twitter_input'):
                # Simple extraction for twitter_input
                twitter_input = values['twitter_input'].strip()
                
                # Handle URLs
                if twitter_input.startswith(('http://', 'https://')):
                    import re
                    match = re.search(r'(?:twitter\.com|x\.com)/(@?[\w]+)', twitter_input)
                    if match:
                        return match.group(1).lstrip('@')
                    raise ValueError(f'Invalid Twitter URL: {twitter_input}')
                
                # Handle username with or without @
                username = twitter_input.lstrip('@')
                if ':' in username:
                    username = username.split(':')[0]
                return username
            elif not v:
                raise ValueError('Twitter username or twitter_input is required for Twitter sources')
        
        if v and v.startswith('@'):
            return v[1:]
        return v
    
    @validator('url', always=True)
    def generate_url(cls, v, values):
        if values.get('source_type') == SourceType.TWITTER:
            username = values.get('twitter_username')
            if username:
                return f"https://twitter.com/{username.lstrip('@')}"
        elif not v:
            raise ValueError('URL is required for website sources')
        return v