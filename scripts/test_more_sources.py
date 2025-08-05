import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from typing import List, Dict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.supabase_client import SupabaseService
from src.services.firecrawl_service import FirecrawlService
from src.services.openai_service import OpenAIService

class TestNewsletterWorkflow:
    def __init__(self):
        self.supabase = SupabaseService()
        self.firecrawl = FirecrawlService()
        self.openai = OpenAIService()
    
    async def process_source(self, source: Dict) -> List[Dict]:
        print(f"\nProcessing source: {source['name']} - {source['url']}")
        
        homepage_result = await self.firecrawl.scrape_homepage(source['url'])
        if not homepage_result['success']:
            print(f"Failed to scrape {source['name']}: {homepage_result.get('error')}")
            return []
        
        # Modified to accept articles from last 7 days
        articles = await self.filter_recent_articles(
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
    
    async def filter_recent_articles(self, markdown_content: str, source_url: str) -> List[Dict]:
        # Get dates for last 7 days
        dates = []
        for i in range(7):
            d = date.today() - timedelta(days=i)
            dates.append(d.strftime('%Y-%m-%d'))
        
        dates_str = ', '.join(dates)
        
        system_prompt = f"""You are an AI news curator. Extract articles from the given markdown content that:
1. Are related to AI, machine learning, LLMs, or artificial intelligence
2. Were published in the last 7 days (acceptable dates: {dates_str}) or don't have a clear date (assume they're recent)
3. Have both a headline and a link

Return a JSON array of objects with: headline, link (absolute URL), and date (use today's date if not specified).
Only return the JSON array, no other text. Format: {{"articles": [...]}}"""

        user_prompt = f"""Extract AI-related articles from this content:
Source URL: {source_url}
Content:
{markdown_content[:10000]}"""

        try:
            response = await self.openai.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            content = response.choices[0].message.content
            result = json.loads(content)
            
            articles = result.get('articles', [])
            if not isinstance(articles, list):
                articles = []
            
            # Fix relative URLs
            for article in articles:
                if not article.get('link', '').startswith('http'):
                    if source_url.endswith('/'):
                        article['link'] = source_url + article['link'].lstrip('/')
                    else:
                        article['link'] = source_url + '/' + article['link'].lstrip('/')
            
            return articles
            
        except Exception as e:
            print(f"Error filtering articles: {e}")
            return []
    
    async def enrich_article(self, article: Dict) -> None:
        print(f"Enriching article: {article['headline'][:60]}...")
        
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
    
    async def run_test_workflow(self):
        print("Starting test newsletter workflow for last 7 days...")
        print(f"Current date: {date.today()}")
        
        sources = await self.supabase.get_active_sources()
        print(f"\nFound {len(sources)} active sources")
        
        # Process sources 5-10 for more variety
        test_sources = sources[5:10]
        
        all_articles = []
        for source in test_sources:
            articles = await self.process_source(source)
            all_articles.extend(articles)
        
        print(f"\n{'='*60}")
        print(f"Collected {len(all_articles)} new articles")
        print(f"{'='*60}\n")
        
        # Enrich articles
        if all_articles:
            print("Starting article enrichment...")
            enrichment_tasks = [self.enrich_article(article) for article in all_articles[:15]]  # Process up to 15
            await asyncio.gather(*enrichment_tasks)
        
        # Get all recent AI-related articles
        recent_articles = []
        for i in range(7):
            d = date.today() - timedelta(days=i)
            query = self.supabase.client.table('articles').select('*').eq('published_at', d).eq('is_ai_related', True)
            response = query.execute()
            recent_articles.extend(response.data)
        
        print(f"\nFound {len(recent_articles)} AI-related articles from last 7 days")
        
        # Get enriched articles with summaries
        enriched_articles = []
        for article in recent_articles:
            if article.get('summary'):
                source = next((s for s in sources if s['id'] == article['source_id']), None)
                article['source_name'] = source['name'] if source else 'Unknown'
                enriched_articles.append(article)
        
        print(f"Found {len(enriched_articles)} enriched articles with summaries")
        
        # Sort by summary quality/length
        enriched_articles.sort(key=lambda x: len(x.get('summary', '')), reverse=True)
        
        if enriched_articles:
            # Generate newsletter
            newsletter = await self.openai.generate_newsletter(enriched_articles[:10])
            
            print(f"\n{'='*60}")
            print("GENERATED NEWSLETTER")
            print(f"{'='*60}")
            print(f"Subject: {newsletter['subject']}")
            print(f"\nContent Preview:\n{newsletter['content'][:1000]}...")
            print(f"{'='*60}\n")
            
            # Save newsletter
            article_ids = [article['id'] for article in enriched_articles[:10]]
            saved_newsletter = await self.supabase.create_newsletter(
                newsletter['subject'],
                newsletter['content'],
                article_ids
            )
            
            if saved_newsletter:
                print(f"Newsletter saved to database with ID: {saved_newsletter['id']}")
        else:
            print("No enriched articles available for newsletter")

async def main():
    workflow = TestNewsletterWorkflow()
    await workflow.run_test_workflow()

if __name__ == "__main__":
    asyncio.run(main())