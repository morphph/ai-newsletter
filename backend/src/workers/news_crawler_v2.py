"""
Enhanced News Crawler with Three-Stage Pipeline
Stage 1: Collect headlines and URLs (fast)
Stage 2: Fetch full content (parallel)
Stage 3: Summarize content (batch processing)
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import sys
import os
import logging
from uuid import uuid4

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.supabase_client import SupabaseService
from src.services.firecrawl_service import FirecrawlService
from src.services.openai_service import OpenAIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedNewsCrawler:
    def __init__(self):
        self.supabase = SupabaseService()
        self.firecrawl = FirecrawlService()
        self.openai = OpenAIService()
        self.batch_id = str(uuid4())
        self.source_stats = {}
        
    async def stage1_collect_headlines(self) -> List[Dict]:
        """Stage 1: Collect today's AI headlines from all sources"""
        logger.info(f"=== STAGE 1: Collecting Headlines (Batch: {self.batch_id}) ===")
        
        sources = await self.supabase.get_active_sources()
        logger.info(f"Processing {len(sources)} active sources")
        
        all_articles = []
        
        for source in sources:
            try:
                logger.info(f"Scraping {source['name']}...")
                
                # Scrape homepage
                homepage_result = await self.firecrawl.scrape_homepage(source['url'])
                
                if not homepage_result['success']:
                    logger.error(f"Failed to scrape {source['name']}: {homepage_result.get('error')}")
                    self.source_stats[source['name']] = {'status': 'failed', 'error': homepage_result.get('error')}
                    continue
                
                # Filter for today's AI articles only
                articles = await self.openai.filter_ai_articles(
                    homepage_result['markdown'],
                    source['url']
                )
                
                # Process and save articles
                new_articles = 0
                for article in articles:
                    # Enhanced deduplication - check both URL and headline
                    exists = await self.supabase.check_article_exists(article['link'])
                    
                    if not exists:
                        article_data = {
                            'source_id': source['id'],
                            'headline': article['headline'],
                            'url': article['link'],
                            'published_at': article.get('date', date.today().isoformat()),
                            'processing_stage': 'pending_enrichment',
                            'crawl_batch_id': self.batch_id,
                            'confidence': article.get('confidence', 'low')
                        }
                        
                        saved = await self.supabase.insert_article(article_data)
                        if saved:
                            all_articles.append(saved)
                            new_articles += 1
                
                self.source_stats[source['name']] = {
                    'status': 'success',
                    'articles_found': len(articles),
                    'new_articles': new_articles
                }
                logger.info(f"✓ {source['name']}: {new_articles} new articles")
                
            except Exception as e:
                logger.error(f"Error processing {source['name']}: {str(e)}")
                self.source_stats[source['name']] = {'status': 'error', 'error': str(e)}
        
        logger.info(f"Stage 1 complete: {len(all_articles)} total new articles")
        return all_articles
    
    async def stage2_fetch_content(self, articles: List[Dict]) -> List[Dict]:
        """Stage 2: Fetch full content for articles in parallel"""
        logger.info(f"=== STAGE 2: Fetching Full Content ({len(articles)} articles) ===")
        
        if not articles:
            return []
        
        # Process in batches to avoid overwhelming the API
        batch_size = 5
        enriched_articles = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            tasks = []
            
            for article in batch:
                tasks.append(self._fetch_single_article(article))
            
            results = await asyncio.gather(*tasks)
            enriched_articles.extend([r for r in results if r])
            
            logger.info(f"Batch {i//batch_size + 1}: Fetched {len([r for r in results if r])} articles")
            
            # Small delay between batches
            if i + batch_size < len(articles):
                await asyncio.sleep(2)
        
        logger.info(f"Stage 2 complete: {len(enriched_articles)} articles enriched")
        return enriched_articles
    
    async def _fetch_single_article(self, article: Dict) -> Optional[Dict]:
        """Fetch content for a single article"""
        try:
            result = await self.firecrawl.scrape_article(article['url'])
            
            if result['success'] and result['markdown']:
                # Update article with full content
                await self.supabase.update_article_full_content(
                    article['id'],
                    result['markdown']
                )
                
                # Update processing stage
                self.supabase.client.table('articles').update({
                    'processing_stage': 'pending_summary',
                    'full_content': result['markdown'][:50000]  # Limit content size
                }).eq('id', article['id']).execute()
                
                article['full_content'] = result['markdown']
                return article
                
        except Exception as e:
            logger.error(f"Error fetching article {article['id']}: {str(e)}")
        
        return None
    
    async def stage3_summarize(self, articles: List[Dict]) -> List[Dict]:
        """Stage 3: Generate summaries for articles"""
        logger.info(f"=== STAGE 3: Summarizing ({len(articles)} articles) ===")
        
        if not articles:
            return []
        
        summarized = []
        
        for article in articles:
            try:
                if not article.get('full_content'):
                    continue
                
                # Generate summary
                summary_result = await self.openai.summarize_article(
                    article['full_content'],
                    article['headline']
                )
                
                # Update article with summary
                await self.supabase.update_article_summary(
                    article['id'],
                    summary_result['summary'],
                    summary_result['is_ai_related']
                )
                
                # Mark as completed
                self.supabase.client.table('articles').update({
                    'processing_stage': 'completed'
                }).eq('id', article['id']).execute()
                
                article['summary'] = summary_result['summary']
                article['is_ai_related'] = summary_result['is_ai_related']
                summarized.append(article)
                
                logger.info(f"✓ Summarized: {article['headline'][:60]}...")
                
            except Exception as e:
                logger.error(f"Error summarizing article {article['id']}: {str(e)}")
        
        logger.info(f"Stage 3 complete: {len(summarized)} articles summarized")
        return summarized
    
    async def run_full_pipeline(self):
        """Run the complete three-stage pipeline"""
        start_time = datetime.now()
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting Enhanced News Crawler Pipeline")
        logger.info(f"Batch ID: {self.batch_id}")
        logger.info(f"Start Time: {start_time}")
        logger.info(f"{'='*60}\n")
        
        try:
            # Stage 1: Collect headlines
            articles = await self.stage1_collect_headlines()
            
            # Stage 2: Fetch content (only for new articles)
            if articles:
                enriched = await self.stage2_fetch_content(articles)
                
                # Stage 3: Summarize
                if enriched:
                    await self.stage3_summarize(enriched)
            
            # Generate summary report
            self._generate_report(start_time)
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            raise
    
    async def resume_incomplete(self):
        """Resume processing for incomplete articles from previous runs"""
        logger.info("Resuming incomplete articles from previous runs...")
        
        # Find articles pending enrichment
        pending_enrichment = self.supabase.client.table('articles').select('*').eq(
            'processing_stage', 'pending_enrichment'
        ).execute()
        
        if pending_enrichment.data:
            logger.info(f"Found {len(pending_enrichment.data)} articles pending enrichment")
            enriched = await self.stage2_fetch_content(pending_enrichment.data)
            if enriched:
                await self.stage3_summarize(enriched)
        
        # Find articles pending summary
        pending_summary = self.supabase.client.table('articles').select('*').eq(
            'processing_stage', 'pending_summary'
        ).execute()
        
        if pending_summary.data:
            logger.info(f"Found {len(pending_summary.data)} articles pending summary")
            await self.stage3_summarize(pending_summary.data)
    
    def _generate_report(self, start_time):
        """Generate and log a summary report"""
        duration = datetime.now() - start_time
        
        logger.info(f"\n{'='*60}")
        logger.info("CRAWL SUMMARY REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"Batch ID: {self.batch_id}")
        logger.info(f"Duration: {duration}")
        logger.info(f"\nSource Statistics:")
        
        success_count = 0
        total_articles = 0
        
        for source, stats in self.source_stats.items():
            if stats['status'] == 'success':
                success_count += 1
                total_articles += stats.get('new_articles', 0)
                logger.info(f"  ✓ {source}: {stats['new_articles']} new articles")
            else:
                logger.info(f"  ✗ {source}: {stats['status']} - {stats.get('error', 'Unknown error')}")
        
        logger.info(f"\nTOTAL: {success_count}/{len(self.source_stats)} sources successful")
        logger.info(f"TOTAL: {total_articles} new articles collected")
        logger.info(f"{'='*60}\n")

async def main():
    crawler = EnhancedNewsCrawler()
    
    import argparse
    parser = argparse.ArgumentParser(description='Enhanced AI News Crawler')
    parser.add_argument('--resume', action='store_true', help='Resume incomplete articles')
    parser.add_argument('--stage', choices=['1', '2', '3', 'all'], default='all', 
                       help='Run specific stage or all')
    
    args = parser.parse_args()
    
    if args.resume:
        await crawler.resume_incomplete()
    elif args.stage == 'all':
        await crawler.run_full_pipeline()
    elif args.stage == '1':
        await crawler.stage1_collect_headlines()
    elif args.stage == '2':
        # Get pending enrichment articles
        pending = crawler.supabase.client.table('articles').select('*').eq(
            'processing_stage', 'pending_enrichment'
        ).execute()
        await crawler.stage2_fetch_content(pending.data)
    elif args.stage == '3':
        # Get pending summary articles
        pending = crawler.supabase.client.table('articles').select('*').eq(
            'processing_stage', 'pending_summary'
        ).execute()
        await crawler.stage3_summarize(pending.data)

if __name__ == "__main__":
    asyncio.run(main())