from fastapi import APIRouter, Query
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ..models.source import SourceResponse
from src.services.supabase_client import SupabaseService

router = APIRouter()

@router.get("/", response_model=List[SourceResponse])
async def get_sources(
    active_only: bool = True,
    category: Optional[str] = None
):
    supabase = SupabaseService()
    
    query = supabase.client.table('sources').select('*')
    
    if active_only:
        query = query.eq('active', True)
    
    if category:
        query = query.eq('category', category)
    
    response = query.order('name').execute()
    
    sources = []
    for source in response.data:
        article_count_response = supabase.client.table('articles').select(
            'id', count='exact'
        ).eq('source_id', source['id']).execute()
        
        source_response = SourceResponse(**source)
        source_response.article_count = article_count_response.count or 0
        sources.append(source_response)
    
    return sources

@router.get("/categories")
async def get_categories():
    supabase = SupabaseService()
    
    response = supabase.client.table('sources').select('category').execute()
    
    categories = list(set([
        source['category'] 
        for source in response.data 
        if source.get('category')
    ]))
    
    return {"categories": sorted(categories)}