from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ..models.article import ArticleResponse
from src.services.supabase_client import SupabaseService

router = APIRouter()

@router.get("/", response_model=List[ArticleResponse])
async def get_articles(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = None,
    source_id: Optional[UUID] = None,
    ai_related_only: bool = True,
    days: int = Query(default=7, ge=1, le=30)
):
    supabase = SupabaseService()
    
    since_date = (datetime.now() - timedelta(days=days)).date()
    
    query = supabase.client.table('articles').select(
        '*, sources!inner(name, category, source_type)'
    ).gte('published_at', since_date.isoformat())
    
    if ai_related_only:
        query = query.eq('is_ai_related', True)
    
    if source_id:
        query = query.eq('source_id', str(source_id))
    
    if category:
        query = query.eq('sources.category', category)
    
    query = query.order('published_at', desc=True).range(offset, offset + limit - 1)
    
    response = query.execute()
    
    articles = []
    for article in response.data:
        article_response = ArticleResponse(**article)
        if 'sources' in article:
            article_response.source_name = article['sources']['name']
            article_response.source_category = article['sources']['category']
            article_response.source_type = article['sources'].get('source_type', 'website')
        articles.append(article_response)
    
    return articles

@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: UUID):
    supabase = SupabaseService()
    
    response = supabase.client.table('articles').select(
        '*, sources!inner(name, category, source_type)'
    ).eq('id', str(article_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article = response.data[0]
    
    supabase.client.table('articles').update({
        'view_count': article.get('view_count', 0) + 1
    }).eq('id', str(article_id)).execute()
    
    # Article views tracking removed (no auth)
    
    article_response = ArticleResponse(**article)
    if 'sources' in article:
        article_response.source_name = article['sources']['name']
        article_response.source_category = article['sources']['category']
        article_response.source_type = article['sources'].get('source_type', 'website')
    
    return article_response

# Bookmark endpoints removed (no auth)