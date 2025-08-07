from fastapi import APIRouter, HTTPException, Query
from typing import Dict
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.services.supabase_client import SupabaseService

router = APIRouter()

@router.get("/source-health")
async def get_source_health(
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze")
) -> Dict:
    """Get health statistics for all news sources"""
    supabase = SupabaseService()
    
    try:
        health_report = await supabase.get_source_health(days)
        
        # Calculate overall statistics
        total_sources = len(health_report)
        healthy_sources = sum(
            1 for source in health_report.values() 
            if source['successful_crawls'] > source['failed_crawls']
        )
        
        return {
            "period_days": days,
            "total_sources": total_sources,
            "healthy_sources": healthy_sources,
            "unhealthy_sources": total_sources - healthy_sources,
            "source_details": health_report,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing-status")
async def get_processing_status() -> Dict:
    """Get current article processing status"""
    supabase = SupabaseService()
    
    try:
        # Get counts by processing stage
        response = supabase.client.table('articles').select(
            'processing_stage', count='exact'
        ).execute()
        
        stages = {}
        for row in response.data:
            stage = row.get('processing_stage', 'unknown')
            if stage not in stages:
                stages[stage] = 0
            stages[stage] += 1
        
        # Get today's statistics
        today_response = supabase.client.table('articles').select(
            'id', count='exact'
        ).eq('published_at', datetime.now().date().isoformat()).execute()
        
        return {
            "processing_stages": stages,
            "todays_articles": today_response.count if hasattr(today_response, 'count') else len(today_response.data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-crawl")
async def trigger_manual_crawl(
    stage: str = Query(default="all", description="Which stage to run: 1, 2, 3, or all")
) -> Dict:
    """Manually trigger a crawl (requires authentication in production)"""
    # TODO: Add authentication check here
    
    try:
        # Import and run the crawler
        from src.workers.news_crawler_v2 import EnhancedNewsCrawler
        import asyncio
        
        crawler = EnhancedNewsCrawler()
        
        if stage == "all":
            await crawler.run_full_pipeline()
        elif stage == "1":
            await crawler.stage1_collect_headlines()
        elif stage == "2":
            # Get pending enrichment articles
            pending = crawler.supabase.client.table('articles').select('*').eq(
                'processing_stage', 'pending_enrichment'
            ).execute()
            await crawler.stage2_fetch_content(pending.data)
        elif stage == "3":
            # Get pending summary articles
            pending = crawler.supabase.client.table('articles').select('*').eq(
                'processing_stage', 'pending_summary'
            ).execute()
            await crawler.stage3_summarize(pending.data)
        else:
            raise HTTPException(status_code=400, detail="Invalid stage. Use 1, 2, 3, or all")
        
        return {
            "status": "success",
            "stage_run": stage,
            "batch_id": crawler.batch_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crawl-history")
async def get_crawl_history(days: int = Query(default=7, ge=1, le=30)) -> Dict:
    """Get crawl history and statistics"""
    supabase = SupabaseService()
    
    try:
        since_date = (datetime.now().date() - timedelta(days=days)).isoformat()
        
        # Get articles grouped by crawl batch
        response = supabase.client.table('articles').select(
            'crawl_batch_id, published_at, processing_stage'
        ).gte('published_at', since_date).execute()
        
        batches = {}
        for article in response.data:
            batch_id = article.get('crawl_batch_id', 'unknown')
            if batch_id not in batches:
                batches[batch_id] = {
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'date': article['published_at']
                }
            
            batches[batch_id]['total'] += 1
            if article.get('processing_stage') == 'completed':
                batches[batch_id]['completed'] += 1
            else:
                batches[batch_id]['pending'] += 1
        
        return {
            "period_days": days,
            "total_batches": len(batches),
            "batch_details": batches,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))