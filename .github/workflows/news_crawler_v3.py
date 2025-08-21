"""
Enhanced News Crawler v3 with Separated Twitter/Article Storage
- Tweets go to tweets table
- Articles go to articles table
- Unified processing pipeline for AI relevance
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
from src.services.twitter_supabase_service import TwitterSupabaseService
from src.services.firecrawl_service import FirecrawlService
from src.services.openai_service import OpenAIService
from src.services.twitter_service import TwitterService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedNewsCrawlerV3:
    def __init__(self):
        self.supabase = SupabaseService()
        self.twitter_supabase = TwitterSupabaseService()
        self.firecrawl = FirecrawlService()
        self.openai = OpenAIService()
        self.twitter = TwitterService()
        self.batch_id = str(uuid4())
        self.source_stats = {}
        
    async def run_full_pipeline(self, target_date: date = None):
        """Run the complete pipeline for a specific date"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        logger.info(f"=== Starting Full Pipeline for {target_date} (Batch: {self.batch_id}) ===")
        
        # Stage 1: Collect content from all sources
        all_content = await self.stage1_collect_content(target_date)
        
        # Stage 2: Process AI relevance for all content
        ai_content = await self.stage2_process_ai_relevance(all_content)
        
        # Stage 3: Generate summaries for AI-related content
        summarized_content = await self.stage3_generate_summaries(ai_content)
        
        # Print summary
        self._print_pipeline_summary(summarized_content)
        
        return summarized_content
    
    async def stage1_collect_content(self, target_date: date) -> Dict[str, List]:
        """Stage 1: Collect content from all sources"""
        logger.info(f"=== STAGE 1: Collecting Content from {target_date} ===")
        
        sources = await self.supabase.get_active_sources()
        logger.info(f"Processing {len(sources)} active sources")
        
        collected_content = {
            'tweets': [],
            'articles': []
        }
        
        for source in sources:
            try:
                source_type = source.get('source_type', 'website')
                logger.info(f"Processing {source['name']} (type: {source_type})...")
                
                if source_type == 'twitter':
                    # Process Twitter source
                    tweets = await self._process_twitter_source(source, target_date)
                    collected_content['tweets'].extend(tweets)
                    
                    self.source_stats[source['name']] = {
                        'status': 'success',
                        'type': 'twitter',
                        'items_collected': len(tweets)
                    }
                else:
                    # Process website source
                    articles = await self._process_website_source(source, target_date)
                    collected_content['articles'].extend(articles)
                    
                    self.source_stats[source['name']] = {
                        'status': 'success',
                        'type': 'website',
                        'items_collected': len(articles)
                    }
                    
            except Exception as e:
                logger.error(f"Error processing {source['name']}: {str(e)}")
                self.source_stats[source['name']] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        logger.info(f"Stage 1 complete: {len(collected_content['tweets'])} tweets, {len(collected_content['articles'])} articles")
        return collected_content
    
    async def _process_twitter_source(self, source: Dict, target_date: date) -> List[Dict]:
        """Process a Twitter source and return tweets for storage"""
        username = source.get('twitter_username')
        if not username:
            logger.error(f"Twitter source {source['name']} missing username")
            return []
        
        # Fetch tweets for the target date
        raw_tweets = await self.twitter.fetch_tweets_for_date(username, target_date)
        
        # Process tweets for storage in tweets table
        processed_tweets = []
        for tweet_data in raw_tweets:
            # Add source_id to tweet data
            tweet_data['source_id'] = source['id']
            
            # Store tweet in tweets table
            saved_tweet = await self.twitter_supabase.insert_tweet(tweet_data)
            if saved_tweet:
                processed_tweets.append(saved_tweet)
        
        logger.info(f"  ✓ {source['name']}: {len(processed_tweets)} tweets stored")
        return processed_tweets
    
    async def _process_website_source(self, source: Dict, target_date: date) -> List[Dict]:
        """Process a website source and return articles"""
        articles = []
        
        try:
            # Scrape homepage
            homepage_result = await self.firecrawl.scrape_homepage(source['url'])
            
            if not homepage_result['success']:
                logger.error(f"Failed to scrape {source['name']}: {homepage_result.get('error')}")
                return []
            
            # Extract article links
            article_links = await self.firecrawl.extract_article_links(
                homepage_result.get('markdown', ''),
                source['url']
            )
            
            logger.info(f"  Found {len(article_links)} links from {source['name']}")
            
            # Filter and save articles for the target date
            for link in article_links[:20]:  # Limit to 20 articles per source
                try:
                    # Check if article already exists
                    exists = await self.supabase.check_article_exists(link['url'])
                    if not exists:
                        article_data = {
                            'source_id': source['id'],
                            'headline': link['title'],
                            'url': link['url'],
                            'published_at': target_date.isoformat(),
                            'processing_stage': 'pending_enrichment',
                            'crawl_batch_id': self.batch_id
                        }
                        
                        # Save to articles table
                        saved = await self.supabase.insert_article(article_data)
                        if saved:
                            articles.append(saved)
                            
                except Exception as e:
                    logger.error(f"Error processing article {link['url']}: {str(e)}")
            
            logger.info(f"  ✓ {source['name']}: {len(articles)} new articles stored")
            
        except Exception as e:
            logger.error(f"Error processing website {source['name']}: {str(e)}")
        
        return articles
    
    async def stage2_process_ai_relevance(self, content: Dict) -> Dict:
        """Stage 2: Process AI relevance for all content"""
        logger.info("=== STAGE 2: Processing AI Relevance ===")
        
        ai_content = {
            'tweets': [],
            'articles': []
        }
        
        # Process tweets for AI relevance
        logger.info(f"Checking AI relevance for {len(content['tweets'])} tweets...")
        for tweet in content['tweets']:
            try:
                is_ai = await self.openai.check_content_ai_relevance(
                    tweet.get('content', ''),
                    f"@{tweet['author_username']}"
                )
                
                if is_ai:
                    # Update tweet as AI-related
                    await self.twitter_supabase.mark_tweet_ai_processed(
                        tweet['tweet_id'],
                        {'is_ai_related': True}
                    )
                    ai_content['tweets'].append(tweet)
                    
            except Exception as e:
                logger.error(f"Error checking AI relevance for tweet {tweet['tweet_id']}: {str(e)}")
        
        # Process articles for AI relevance
        logger.info(f"Checking AI relevance for {len(content['articles'])} articles...")
        for article in content['articles']:
            try:
                # Fetch full content if not already present
                if not article.get('full_content'):
                    full_content_result = await self.firecrawl.scrape_article(article['url'])
                    if full_content_result['success']:
                        article['full_content'] = full_content_result.get('markdown', '')[:10000]
                        await self.supabase.update_article_content(
                            article['id'],
                            article['full_content']
                        )
                
                # Check AI relevance
                is_ai = await self.openai.check_content_ai_relevance(
                    article.get('full_content', article.get('headline', '')),
                    article.get('headline', '')
                )
                
                if is_ai:
                    # Update article as AI-related
                    await self.supabase.update_article_ai_status(article['id'], True)
                    ai_content['articles'].append(article)
                    
            except Exception as e:
                logger.error(f"Error processing article {article['url']}: {str(e)}")
        
        logger.info(f"Stage 2 complete: {len(ai_content['tweets'])} AI tweets, {len(ai_content['articles'])} AI articles")
        return ai_content
    
    async def stage3_generate_summaries(self, content: Dict) -> Dict:
        """Stage 3: Generate summaries for AI-related content"""
        logger.info("=== STAGE 3: Generating Summaries ===")
        
        summarized_content = {
            'tweets': [],
            'articles': []
        }
        
        # Generate summaries for tweets (batch processing)
        if content['tweets']:
            logger.info(f"Generating summaries for {len(content['tweets'])} AI tweets...")
            
            # Batch tweets by author for context
            tweets_by_author = {}
            for tweet in content['tweets']:
                author = tweet['author_username']
                if author not in tweets_by_author:
                    tweets_by_author[author] = []
                tweets_by_author[author].append(tweet)
            
            for author, author_tweets in tweets_by_author.items():
                try:
                    # Generate batch summary for author's tweets
                    combined_content = "\n\n".join([t['content'] for t in author_tweets[:5]])
                    summary = await self.openai.generate_tweet_summary(combined_content, author)
                    
                    # Update each tweet with summary
                    for tweet in author_tweets:
                        await self.twitter_supabase.mark_tweet_ai_processed(
                            tweet['tweet_id'],
                            {
                                'summary': summary,
                                'is_ai_related': True,
                                'ai_tags': await self.openai.extract_tags(tweet['content'])
                            }
                        )
                        tweet['ai_summary'] = summary
                        summarized_content['tweets'].append(tweet)
                        
                except Exception as e:
                    logger.error(f"Error generating summary for @{author}: {str(e)}")
        
        # Generate summaries for articles
        if content['articles']:
            logger.info(f"Generating summaries for {len(content['articles'])} AI articles...")
            
            for article in content['articles']:
                try:
                    summary = await self.openai.generate_summary(
                        article.get('full_content', article.get('headline', ''))
                    )
                    
                    # Update article with summary
                    await self.supabase.update_article_summary(article['id'], summary)
                    article['summary'] = summary
                    summarized_content['articles'].append(article)
                    
                except Exception as e:
                    logger.error(f"Error generating summary for {article['url']}: {str(e)}")
        
        logger.info(f"Stage 3 complete: Summaries generated for {len(summarized_content['tweets']) + len(summarized_content['articles'])} items")
        return summarized_content
    
    def _print_pipeline_summary(self, content: Dict):
        """Print summary of the pipeline execution"""
        print("\n" + "="*60)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*60)
        
        print(f"\nBatch ID: {self.batch_id}")
        print(f"\nContent Processed:")
        print(f"  - AI Tweets: {len(content.get('tweets', []))}")
        print(f"  - AI Articles: {len(content.get('articles', []))}")
        
        print(f"\nSource Statistics:")
        for source, stats in self.source_stats.items():
            status_icon = "✓" if stats['status'] == 'success' else "✗"
            print(f"  {status_icon} {source}: {stats.get('items_collected', 0)} items")
            if stats['status'] == 'error':
                print(f"    Error: {stats['error']}")
        
        print("\n" + "="*60)

async def main():
    """Run the crawler for yesterday's content"""
    crawler = EnhancedNewsCrawlerV3()
    
    try:
        yesterday = date.today() - timedelta(days=1)
        results = await crawler.run_full_pipeline(yesterday)
        
        print(f"\n✅ Crawler completed successfully")
        print(f"   - {len(results.get('tweets', []))} AI tweets")
        print(f"   - {len(results.get('articles', []))} AI articles")
        
    except Exception as e:
        logger.error(f"Crawler failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())