import asyncio
from typing import List, Dict
from datetime import date
from src.services.supabase_client import SupabaseService
from src.services.firecrawl_service import FirecrawlService
from src.services.openai_service import OpenAIService

class NewsletterWorkflow:
    def __init__(self):
        self.supabase = SupabaseService()
        self.firecrawl = FirecrawlService()
        self.openai = OpenAIService()
    
    async def process_source(self, source: Dict) -> List[Dict]:
        print(f"Processing source: {source['name']} - {source['url']}")
        
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
                print(f"Article already exists: {article['headline']}")
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
                print(f"Saved article: {article['headline']}")
        
        return processed_articles
    
    async def enrich_article(self, article: Dict) -> None:
        print(f"Enriching article: {article['headline']}")
        
        article_result = await self.firecrawl.scrape_article(article['url'])
        if not article_result['success']:
            print(f"Failed to scrape article: {article_result.get('error')}")
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
    
    async def run_daily_workflow(self):
        print("Starting daily newsletter workflow...")
        
        sources = await self.supabase.get_active_sources()
        print(f"Found {len(sources)} active sources")
        
        all_articles = []
        for source in sources:
            articles = await self.process_source(source)
            all_articles.extend(articles)
        
        print(f"Collected {len(all_articles)} new articles")
        
        enrichment_tasks = [self.enrich_article(article) for article in all_articles]
        await asyncio.gather(*enrichment_tasks)
        
        today_articles = await self.supabase.get_today_articles(ai_related_only=True)
        
        if not today_articles:
            print("No AI-related articles found for today")
            return
        
        enriched_articles = []
        for article in today_articles:
            if article.get('summary'):
                source = next((s for s in sources if s['id'] == article['source_id']), None)
                article['source_name'] = source['name'] if source else 'Unknown'
                enriched_articles.append(article)
        
        enriched_articles.sort(key=lambda x: len(x.get('summary', '')), reverse=True)
        
        if enriched_articles:
            newsletter = await self.openai.generate_newsletter(enriched_articles[:10])
            
            article_ids = [article['id'] for article in enriched_articles[:10]]
            saved_newsletter = await self.supabase.create_newsletter(
                newsletter['subject'],
                newsletter['content'],
                article_ids
            )
            
            if saved_newsletter:
                print(f"Newsletter created: {newsletter['subject']}")
                print(f"Included {len(article_ids)} articles")
            else:
                print("Failed to save newsletter")
        else:
            print("No enriched articles available for newsletter")
        
        print("Daily workflow completed!")

async def main():
    workflow = NewsletterWorkflow()
    await workflow.run_daily_workflow()

if __name__ == "__main__":
    asyncio.run(main())