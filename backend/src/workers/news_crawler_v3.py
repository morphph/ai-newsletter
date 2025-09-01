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
from src.utils.content_filters import ContentFilter

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
        self.pipeline_stats = {
            'tweets_collected': 0,
            'tweets_date_matched': 0,
            'articles_checked': 0,
            'articles_pre_filtered': 0,
            'articles_scraped': 0,
            'articles_date_matched': 0,
            'articles_collected': 0,
            'ai_tweets': 0,
            'ai_articles': 0,
            'summaries_generated': 0,
            'api_calls_saved': 0
        }
        
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
        """Process Twitter source: Fetch yesterday's tweets -> GPT filter -> Store only AI tweets"""
        username = source.get('twitter_username')
        if not username:
            logger.error(f"Twitter source {source['name']} missing username")
            return []
        
        # Validate target_date is not too far in the past or future
        days_diff = (date.today() - target_date).days
        if days_diff > 30:
            logger.warning(f"Target date {target_date} is {days_diff} days old - may not find tweets")
        elif days_diff < 0:
            logger.error(f"Target date {target_date} is in the future!")
            return []
        
        # Step 1: Fetch tweets for the target date
        raw_tweets = await self.twitter.fetch_tweets_for_date(username, target_date)
        
        # Update statistics
        self.pipeline_stats['tweets_date_matched'] += len(raw_tweets)
        
        if not raw_tweets:
            logger.info(f"  No tweets from {target_date} for @{username}")
            return []
        
        logger.info(f"  Found {len(raw_tweets)} tweets from {target_date}")
        
        # Step 2: Batch evaluate with GPT for AI relevance
        ai_tweets = await self.openai.evaluate_tweets_batch(raw_tweets, target_date)
        
        logger.info(f"  GPT identified {len(ai_tweets)} AI-related tweets")
        
        # Step 3: Store only AI-related tweets
        processed_tweets = []
        for tweet_data in ai_tweets:
            # Add metadata
            tweet_data['source_id'] = source['id']
            tweet_data['is_ai_related'] = True  # Mark as AI-related immediately
            
            # Store tweet in tweets table
            saved_tweet = await self.twitter_supabase.insert_tweet(tweet_data)
            if saved_tweet:
                processed_tweets.append(saved_tweet)
                self.pipeline_stats['ai_tweets'] += 1
        
        self.pipeline_stats['tweets_collected'] += len(processed_tweets)
        logger.info(f"  ✓ {source['name']}: {len(processed_tweets)} AI tweets stored (filtered from {len(raw_tweets)})")
        
        return processed_tweets
    
    async def _process_website_source(self, source: Dict, target_date: date) -> List[Dict]:
        """Process website with new flow: Firecrawl homepage -> GPT combined filter -> Firecrawl articles"""
        articles = []
        articles_total = 0
        articles_gpt_filtered = 0
        articles_scraped = 0
        
        try:
            # Step 1: Scrape homepage
            homepage_result = await self.firecrawl.scrape_homepage(source['url'])
            
            if not homepage_result['success']:
                logger.error(f"Failed to scrape {source['name']}: {homepage_result.get('error')}")
                return []
            
            # Step 2: Extract ALL article links (no filtering yet!)
            article_links = await self.firecrawl.extract_article_links(
                homepage_result.get('markdown', ''),
                source['url']
            )
            
            articles_total = len(article_links)
            logger.info(f"  Found {articles_total} total links from {source['name']}")
            
            if not article_links:
                logger.info(f"  No articles found on {source['name']} homepage")
                return []
            
            # Step 3: Send ALL articles to GPT for combined date + AI filtering
            # GPT will identify articles that are BOTH from target_date AND AI-related
            gpt_filtered_articles = await self.openai.evaluate_articles_date_and_ai(
                article_links,
                target_date=target_date
            )
            
            articles_gpt_filtered = len(gpt_filtered_articles)
            logger.info(f"  GPT identified {articles_gpt_filtered} articles from {target_date} that are AI-related")
            
            if not gpt_filtered_articles:
                logger.info(f"  No AI articles from {target_date} found on {source['name']}")
                return []
            
            # Step 4: Scrape only GPT-approved articles (both date AND AI matched)
            for article in gpt_filtered_articles[:10]:  # Limit to 10 articles per source
                try:
                    # Check if article already exists
                    exists = await self.supabase.check_article_exists(article['url'])
                    if exists:
                        logger.debug(f"  Article already exists: {article['url']}")
                        continue
                    
                    # Scrape the GPT-approved article
                    articles_scraped += 1
                    article_result = await self.firecrawl.scrape_article(article['url'])
                    
                    if not article_result['success']:
                        logger.debug(f"  Failed to scrape article {article['url']}")
                        continue
                    
                    # Log GPT's confidence level for debugging
                    if article.get('gpt_confidence'):
                        logger.debug(f"  Article confidence: {article['gpt_confidence']} - {article.get('gpt_reason', '')}")
                    
                    # Store the article (GPT already verified both date AND AI relevance)
                    full_content = article_result.get('markdown', '')[:10000]
                    article_data = {
                        'source_id': source['id'],
                        'headline': article_result.get('title') or article.get('title', 'Untitled'),
                        'url': article['url'],
                        'published_at': target_date.isoformat(),
                        'full_content': full_content,
                        'is_ai_related': True,  # GPT confirmed this
                        'processing_stage': 'pending_summary',
                        'crawl_batch_id': self.batch_id
                    }
                    
                    # Save to articles table
                    saved = await self.supabase.insert_article(article_data)
                    if saved:
                        articles.append(saved)
                        self.pipeline_stats['ai_articles'] += 1
                        logger.debug(f"  ✓ Saved article: {article['url'][:80]}...")
                    
                            
                except Exception as e:
                    logger.error(f"Error processing article {article['url']}: {str(e)}")
            
            # Update pipeline statistics with new flow metrics
            self.pipeline_stats['articles_checked'] += articles_total  # Total found on homepage
            self.pipeline_stats['articles_date_matched'] += articles_gpt_filtered  # GPT found matching date
            self.pipeline_stats['articles_pre_filtered'] += articles_gpt_filtered  # GPT filtered (date + AI)
            self.pipeline_stats['articles_scraped'] += articles_scraped  # Actually scraped
            self.pipeline_stats['articles_collected'] += len(articles)  # Successfully saved
            # Calculate efficiency - we only scrape what GPT approves
            self.pipeline_stats['api_calls_saved'] += max(0, articles_total - articles_scraped)
            
            logger.info(f"  ✓ {source['name']}: {len(articles)} AI articles stored")
            logger.info(f"    New flow: {articles_total} total → {articles_gpt_filtered} GPT-filtered (date+AI) → {articles_scraped} scraped → {len(articles)} saved")
            
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
        
        # Process tweets for AI relevance (most should already be marked from Stage 1)
        logger.info(f"Verifying AI relevance for {len(content['tweets'])} tweets...")
        for tweet in content['tweets']:
            try:
                # Skip if already marked as AI-related (from new optimized flow)
                if tweet.get('is_ai_related'):
                    ai_content['tweets'].append(tweet)
                    continue
                
                # For tweets not pre-processed (legacy flow or missed tweets)
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
                    self.pipeline_stats['ai_tweets'] += 1
                    
            except Exception as e:
                logger.error(f"Error checking AI relevance for tweet {tweet['tweet_id']}: {str(e)}")
        
        # Process articles for AI relevance (most should already be marked)
        logger.info(f"Verifying AI relevance for {len(content['articles'])} articles...")
        for article in content['articles']:
            try:
                # Skip if already marked as AI-related (from optimized flow)
                if article.get('is_ai_related'):
                    ai_content['articles'].append(article)
                    continue
                
                # For articles not pre-processed (shouldn't happen with new flow)
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
                    self.pipeline_stats['ai_articles'] += 1
                    
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
                        self.pipeline_stats['summaries_generated'] += 1
                        
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
                    
                    # Update article with summary (already confirmed as AI-related)
                    await self.supabase.update_article_summary(article['id'], summary, is_ai_related=True)
                    article['summary'] = summary
                    summarized_content['articles'].append(article)
                    self.pipeline_stats['summaries_generated'] += 1
                    
                except Exception as e:
                    logger.error(f"Error generating summary for {article['url']}: {str(e)}")
        
        logger.info(f"Stage 3 complete: Summaries generated for {len(summarized_content['tweets']) + len(summarized_content['articles'])} items")
        return summarized_content
    
    def _print_pipeline_summary(self, content: Dict):
        """Print summary of the pipeline execution"""
        print("\n" + "="*70)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*70)
        
        print(f"\nBatch ID: {self.batch_id}")
        
        print(f"\n📊 FILTERING STATISTICS:")
        print(f"  Twitter:")
        print(f"    - Tweets matching target date: {self.pipeline_stats['tweets_date_matched']}")
        print(f"    - Tweets successfully stored: {self.pipeline_stats['tweets_collected']}")
        print(f"  Articles:")
        print(f"    - Total articles found on homepages: {self.pipeline_stats['articles_checked']}")
        print(f"    - Pre-filtered (likely relevant): {self.pipeline_stats['articles_pre_filtered']}")
        print(f"    - Actually scraped (API calls): {self.pipeline_stats['articles_scraped']}")
        print(f"    - Articles matching target date: {self.pipeline_stats['articles_date_matched']}")
        print(f"    - AI articles stored: {self.pipeline_stats['articles_collected']}")
        
        print(f"\n🤖 AI FILTERING STATISTICS:")
        print(f"  - AI-related tweets: {self.pipeline_stats['ai_tweets']}/{self.pipeline_stats['tweets_collected']}")
        print(f"  - AI-related articles: {self.pipeline_stats['ai_articles']}/{self.pipeline_stats['articles_collected']}")
        print(f"  - Summaries generated: {self.pipeline_stats['summaries_generated']}")
        
        print(f"\n💰 EFFICIENCY METRICS:")
        print(f"  - Firecrawl API calls saved: {self.pipeline_stats['api_calls_saved']}")
        if self.pipeline_stats['articles_checked'] > 0:
            efficiency = (self.pipeline_stats['api_calls_saved'] / self.pipeline_stats['articles_checked']) * 100
            print(f"  - API call reduction: {efficiency:.1f}%")
        
        # Calculate filtering efficiency
        if self.pipeline_stats['tweets_collected'] > 0:
            tweet_ai_rate = (self.pipeline_stats['ai_tweets'] / self.pipeline_stats['tweets_collected']) * 100
            print(f"  - Tweet AI relevance rate: {tweet_ai_rate:.1f}%")
        
        if self.pipeline_stats['articles_collected'] > 0:
            article_ai_rate = (self.pipeline_stats['ai_articles'] / self.pipeline_stats['articles_collected']) * 100
            print(f"  - Article AI relevance rate: {article_ai_rate:.1f}%")
        
        if self.pipeline_stats['articles_checked'] > 0:
            date_match_rate = (self.pipeline_stats['articles_date_matched'] / self.pipeline_stats['articles_checked']) * 100
            print(f"  - Article date match rate: {date_match_rate:.1f}%")
        
        print(f"\n📋 SOURCE BREAKDOWN:")
        for source, stats in self.source_stats.items():
            status_icon = "✓" if stats['status'] == 'success' else "✗"
            print(f"  {status_icon} {source}: {stats.get('items_collected', 0)} items")
            if stats['status'] == 'error':
                print(f"    Error: {stats['error']}")
        
        print("\n" + "="*70)

async def main():
    """Run the crawler with optional date parameter"""
    import argparse
    
    parser = argparse.ArgumentParser(description='News Crawler v3')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to crawl in YYYY-MM-DD format (default: yesterday)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for GitHub Actions)'
    )
    
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            print(f"Processing specified date: {target_date}")
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = date.today() - timedelta(days=1)
        print(f"Processing default date (yesterday): {target_date}")
    
    crawler = EnhancedNewsCrawlerV3()
    
    try:
        results = await crawler.run_full_pipeline(target_date)
        
        print(f"\n✅ Crawler completed successfully for {target_date}")
        print(f"   - {len(results.get('tweets', []))} AI tweets")
        print(f"   - {len(results.get('articles', []))} AI articles")
        
    except Exception as e:
        logger.error(f"Crawler failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())