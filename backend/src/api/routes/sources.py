from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ..models.source import SourceResponse, SourceCreate, SourceType
from src.services.supabase_client import SupabaseService

router = APIRouter()

@router.get("/", response_model=List[SourceResponse])
async def get_sources(
    active_only: bool = True,
    category: Optional[str] = None,
    source_type: Optional[SourceType] = None
):
    supabase = SupabaseService()
    
    query = supabase.client.table('sources').select('*')
    
    if active_only:
        query = query.eq('active', True)
    
    if category:
        query = query.eq('category', category)
    
    if source_type:
        query = query.eq('source_type', source_type.value)
    
    response = query.order('name').execute()
    
    sources = []
    for source in response.data:
        article_count_response = supabase.client.table('articles').select(
            'id', count='exact'
        ).eq('source_id', source['id']).execute()
        
        # Set default source_type if not present
        if 'source_type' not in source:
            source['source_type'] = 'website'
        
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

@router.post("/", response_model=SourceResponse)
async def create_source(source: SourceCreate):
    """Create a new source (website or Twitter)"""
    supabase = SupabaseService()
    
    # Check if Twitter source already exists
    if source.source_type == SourceType.TWITTER:
        if not source.twitter_username:
            raise HTTPException(status_code=400, detail="Twitter username is required for Twitter sources")
        
        existing = supabase.client.table('sources').select('*').eq(
            'twitter_username', source.twitter_username
        ).execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail=f"Twitter source @{source.twitter_username} already exists")
    
    # Check if website URL already exists
    elif source.source_type == SourceType.WEBSITE:
        if not source.url:
            raise HTTPException(status_code=400, detail="URL is required for website sources")
        
        existing = supabase.client.table('sources').select('*').eq(
            'url', source.url
        ).execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail=f"Website source {source.url} already exists")
    
    # Create source record
    source_data = {
        'id': str(uuid4()),
        'name': source.name,
        'url': source.url,
        'source_type': source.source_type.value,
        'category': source.category,
        'twitter_username': source.twitter_username,
        'active': source.active,
        'created_at': datetime.utcnow().isoformat()
    }
    
    try:
        result = supabase.client.table('sources').insert(source_data).execute()
        if result.data:
            return SourceResponse(**result.data[0], article_count=0)
        else:
            raise HTTPException(status_code=500, detail="Failed to create source")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/twitter", response_model=List[SourceResponse])
async def get_twitter_sources(
    active_only: bool = True
):
    """Get all Twitter sources"""
    return await get_sources(
        active_only=active_only,
        source_type=SourceType.TWITTER
    )

@router.get("/websites", response_model=List[SourceResponse])
async def get_website_sources(
    active_only: bool = True
):
    """Get all website sources"""
    return await get_sources(
        active_only=active_only,
        source_type=SourceType.WEBSITE
    )

@router.patch("/{source_id}/toggle")
async def toggle_source(source_id: str):
    """Toggle source active status"""
    supabase = SupabaseService()
    
    # Get current status
    source = supabase.client.table('sources').select('*').eq('id', source_id).single().execute()
    
    if not source.data:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Toggle status
    new_status = not source.data['active']
    
    result = supabase.client.table('sources').update({
        'active': new_status
    }).eq('id', source_id).execute()
    
    if result.data:
        return {"message": f"Source {'activated' if new_status else 'deactivated'}", "active": new_status}
    else:
        raise HTTPException(status_code=500, detail="Failed to update source")