import asyncio
from typing import List, Dict
from datetime import datetime, date
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.supabase_client import SupabaseService
from src.services.firecrawl_service import FirecrawlService
from src.services.openai_service import OpenAIService

class NewsCrawler:
    def __init__(self):
        self.supabase = SupabaseService()
        self.firecrawl = FirecrawlService()
        self.openai = OpenAIService()
        self.is_running = False
    
    async def process_source(self, source: Dict) -> List[Dict]:
        print(f"[{datetime.now()}] Processing source: {source['name']}")
        
        try:
            homepage_result = await self.firecrawl.scrape_homepage(source['url'])
            if not homepage_result['success']:
                print(f"Failed to scrape {source['name']}: {homepage_result.get('error')}")
                return []
            
            articles = await self.openai.filter_ai_articles(
                homepage_result['markdown'],
                source['url']
            )
            
            processed_articles = []
            for article in articles:
                if await self.supabase.check_article_exists(article['link']):
                    continue
                
                article_data = {
                    'source_id': source['id'],
                    'headline': article['headline'],
                    'url': article['link'],
                    'published_at': article.get('date', date.today().isoformat())
                }
                
                saved_article = await self.supabase.insert_article(article_data)
                if saved_article:
                    processed_articles.append(saved_article)
                    print(f"  ✓ New article: {article['headline'][:60]}...")
            
            return processed_articles
            
        except Exception as e:
            print(f"Error processing source {source['name']}: {str(e)}")
            return []
    
    async def enrich_article(self, article: Dict) -> None:
        try:
            article_result = await self.firecrawl.scrape_article(article['url'])
            if not article_result['success']:
                return
            
            if article_result['markdown']:
                await self.supabase.update_article_full_content(
                    article['id'],
                    article_result['markdown']
                )
            
            summary_result = await self.openai.summarize_article(
                article_result['markdown'],
                article['headline']
            )
            
            await self.supabase.update_article_summary(
                article['id'],
                summary_result['summary'],
                summary_result['is_ai_related']
            )
            
            # Extract image URL if available
            if 'image_url' in summary_result:
                self.supabase.client.table('articles').update({
                    'image_url': summary_result['image_url']
                }).eq('id', article['id']).execute()
                
        except Exception as e:
            print(f"Error enriching article {article['id']}: {str(e)}")
    
    async def crawl_once(self):
        print(f"\n{'='*60}")
        print(f"Starting news crawl at {datetime.now()}")
        print(f"{'='*60}\n")
        
        sources = await self.supabase.get_active_sources()
        print(f"Found {len(sources)} active sources")
        
        all_articles = []
        for source in sources:
            articles = await self.process_source(source)
            all_articles.extend(articles)
        
        print(f"\nCollected {len(all_articles)} new articles")
        
        if all_articles:
            print("Enriching articles...")
            enrichment_tasks = [self.enrich_article(article) for article in all_articles]
            await asyncio.gather(*enrichment_tasks)
            print("Enrichment complete")
        
        print(f"\nCrawl completed at {datetime.now()}")
    
    async def run_continuous(self, interval_minutes: int = 30):
        self.is_running = True
        print(f"Starting continuous crawler (interval: {interval_minutes} minutes)")
        
        while self.is_running:
            try:
                await self.crawl_once()
                print(f"\nNext crawl in {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\nStopping crawler...")
                self.is_running = False
                break
            except Exception as e:
                print(f"Crawler error: {str(e)}")
                print(f"Retrying in {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)
    
    def stop(self):
        self.is_running = False

async def main():
    crawler = NewsCrawler()
    
    import argparse
    parser = argparse.ArgumentParser(description='AI News Crawler')
    parser.add_argument('--once', action='store_true', help='Run crawler once and exit')
    parser.add_argument('--interval', type=int, default=30, help='Crawl interval in minutes (default: 30)')
    
    args = parser.parse_args()
    
    if args.once:
        await crawler.crawl_once()
    else:
        await crawler.run_continuous(args.interval)

if __name__ == "__main__":
    asyncio.run(main())