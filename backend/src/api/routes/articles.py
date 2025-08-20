from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, date
from collections import defaultdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ..models.article import ArticleResponse
from src.services.supabase_client import SupabaseService
from src.services.openai_service import OpenAIService

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
        '*, sources!inner(name, category)'
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
        articles.append(article_response)
    
    return articles

@router.get("/by-day", response_model=Dict[str, Any])
async def get_articles_by_day(
    days: int = Query(default=30, ge=1, le=30)
):
    """Get articles grouped by day with daily summaries"""
    supabase = SupabaseService()
    openai_service = OpenAIService()
    
    since_date = (datetime.now() - timedelta(days=days)).date()
    
    # Get all AI-related articles from the past N days
    response = supabase.client.table('articles').select(
        '*, sources!inner(name, category)'
    ).gte('published_at', since_date.isoformat()).eq('is_ai_related', True).order('published_at', desc=True).execute()
    
    # Group articles by date
    articles_by_day = defaultdict(list)
    for article in response.data:
        pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')).date()
        articles_by_day[pub_date.isoformat()].append(article)
    
    # Generate daily summaries
    daily_summaries = []
    for day, articles in sorted(articles_by_day.items(), reverse=True):
        if not articles:
            daily_summaries.append({
                'date': day,
                'summary': 'not much happened today',
                'article_count': 0,
                'top_stories': []
            })
        else:
            # Get top 3 articles for the day
            top_stories = sorted(articles, key=lambda x: x.get('view_count', 0), reverse=True)[:3]
            
            # Generate a summary if we have articles
            if len(articles) >= 3:
                titles = [a.get('headline', a.get('title', '')) for a in articles[:10]]  # Use top 10 titles for summary
                prompt = f"Given these AI news titles from {day}, create a brief one-line summary (max 100 chars) highlighting the most important developments: {'; '.join(titles)}"
                
                try:
                    summary = await openai_service.generate_summary(prompt, max_tokens=50)
                    # Truncate to ensure it fits
                    if len(summary) > 100:
                        summary = summary[:97] + '...'
                except:
                    # Fallback to using the top article title
                    headline = articles[0].get('headline', articles[0].get('title', 'Unknown'))
                    summary = headline[:97] + '...' if len(headline) > 100 else headline
            else:
                summary = 'not much happened today'
            
            daily_summaries.append({
                'date': day,
                'summary': summary,
                'article_count': len(articles),
                'top_stories': [{'id': str(a['id']), 'title': a.get('headline', a.get('title', ''))} for a in top_stories]
            })
    
    return {
        'days': daily_summaries,
        'total_days': len(daily_summaries)
    }

@router.get("/day/{date_str}", response_model=Dict[str, Any])
async def get_articles_for_day(date_str: str):
    """Get categorized articles for a specific day"""
    supabase = SupabaseService()
    openai_service = OpenAIService()
    
    try:
        target_date = datetime.fromisoformat(date_str).date()
    except:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get articles for the specific day
    next_day = target_date + timedelta(days=1)
    
    response = supabase.client.table('articles').select(
        '*, sources!inner(name, category)'
    ).gte('published_at', target_date.isoformat()).lt('published_at', next_day.isoformat()).eq('is_ai_related', True).order('published_at', desc=True).execute()
    
    if not response.data:
        return {
            'date': date_str,
            'categories': {
                'llm': [],
                'multimodal': [],
                'ai_agents': [],
                'ai_tools': []
            },
            'total_articles': 0
        }
    
    # Categorize articles
    categories = {
        'llm': [],
        'multimodal': [],
        'ai_agents': [],
        'ai_tools': []
    }
    
    for article in response.data:
        # Use OpenAI to categorize if not already categorized
        category = await categorize_article(article, openai_service)
        
        article_data = {
            'id': str(article['id']),
            'title': article.get('headline', article.get('title', '')),
            'summary': article.get('summary', ''),
            'url': article.get('url', ''),
            'source': article.get('sources', {}).get('name', 'Unknown'),
            'published_at': article['published_at']
        }
        
        if category in categories:
            categories[category].append(article_data)
        else:
            # Default to ai_tools if category is unknown
            categories['ai_tools'].append(article_data)
    
    return {
        'date': date_str,
        'categories': categories,
        'total_articles': len(response.data)
    }

async def categorize_article(article: dict, openai_service: OpenAIService) -> str:
    """Categorize an article into one of: llm, multimodal, ai_agents, ai_tools"""
    
    # Check if article mentions specific keywords
    title_lower = article.get('headline', article.get('title', '')).lower()
    content_lower = (article.get('full_content', article.get('content', '')) or '').lower()
    combined_text = title_lower + ' ' + content_lower
    
    # Simple keyword-based categorization
    if any(keyword in combined_text for keyword in ['gpt', 'claude', 'llama', 'mistral', 'gemini', 'language model', 'llm', 'chatbot']):
        return 'llm'
    elif any(keyword in combined_text for keyword in ['image', 'video', 'multimodal', 'vision', 'dall-e', 'midjourney', 'stable diffusion', 'audio']):
        return 'multimodal'
    elif any(keyword in combined_text for keyword in ['agent', 'autogpt', 'babyagi', 'langchain', 'crew', 'autonomous']):
        return 'ai_agents'
    elif any(keyword in combined_text for keyword in ['tool', 'ide', 'cursor', 'copilot', 'v0', 'vercel', 'framework', 'library', 'api']):
        return 'ai_tools'
    
    # If no clear match, use OpenAI for categorization
    try:
        prompt = f"""Categorize this AI news article into EXACTLY ONE of these categories:
        - llm (language models, chatbots, text generation)
        - multimodal (image/video/audio generation or analysis)
        - ai_agents (autonomous agents, agent frameworks)
        - ai_tools (developer tools, IDEs, APIs, frameworks)
        
        Title: {article.get('headline', article.get('title', ''))}
        Summary: {article.get('summary', '')[:200]}
        
        Reply with ONLY the category name (llm, multimodal, ai_agents, or ai_tools)."""
        
        category = await openai_service.generate_summary(prompt, max_tokens=10)
        category = category.strip().lower().replace('_', '_')
        
        if category in ['llm', 'multimodal', 'ai_agents', 'ai_tools']:
            return category
    except:
        pass
    
    # Default fallback
    return 'ai_tools'

@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: UUID):
    supabase = SupabaseService()
    
    response = supabase.client.table('articles').select(
        '*, sources!inner(name, category)'
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
    
    return article_response

# Bookmark endpoints removed (no auth)