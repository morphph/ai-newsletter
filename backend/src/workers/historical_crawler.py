#!/usr/bin/env python3
"""
Historical Data Crawler - Populates news data for past N days
"""

import asyncio
import argparse
import sys
import os
from datetime import date, timedelta
import time
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.workers.news_crawler_v3 import EnhancedNewsCrawlerV3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def crawl_historical_data(days: int = 3, delay_seconds: int = 30):
    """
    Crawl historical data for the specified number of days
    
    Args:
        days: Number of days to go back (default: 3)
        delay_seconds: Delay between processing each day (default: 30)
    """
    print("\n" + "="*70)
    print(f"HISTORICAL DATA CRAWLER - Processing last {days} days")
    print("="*70)
    
    today = date.today()
    successful_days = []
    failed_days = []
    
    for i in range(1, days + 1):
        target_date = today - timedelta(days=i)
        
        print(f"\n[Day {i}/{days}] Processing {target_date}...")
        print("-" * 50)
        
        try:
            # Create a new crawler instance for each day
            crawler = EnhancedNewsCrawlerV3()
            
            # Run the pipeline for this specific date
            results = await crawler.run_full_pipeline(target_date)
            
            tweets_count = len(results.get('tweets', []))
            articles_count = len(results.get('articles', []))
            
            print(f"✅ Successfully processed {target_date}")
            print(f"   - {tweets_count} AI-relevant tweets")
            print(f"   - {articles_count} AI-relevant articles")
            
            successful_days.append({
                'date': target_date,
                'tweets': tweets_count,
                'articles': articles_count
            })
            
            # Add delay between days to avoid rate limiting
            if i < days:
                print(f"\n⏳ Waiting {delay_seconds} seconds before next day...")
                await asyncio.sleep(delay_seconds)
                
        except Exception as e:
            logger.error(f"Failed to process {target_date}: {str(e)}")
            print(f"❌ Failed to process {target_date}: {str(e)}")
            failed_days.append({
                'date': target_date,
                'error': str(e)
            })
            
            # Continue with next day even if this one failed
            continue
    
    # Print final summary
    print("\n" + "="*70)
    print("HISTORICAL CRAWL SUMMARY")
    print("="*70)
    
    if successful_days:
        print(f"\n✅ Successfully processed {len(successful_days)} days:")
        total_tweets = 0
        total_articles = 0
        for day_data in successful_days:
            print(f"   - {day_data['date']}: {day_data['tweets']} tweets, {day_data['articles']} articles")
            total_tweets += day_data['tweets']
            total_articles += day_data['articles']
        print(f"\n   Total: {total_tweets} tweets, {total_articles} articles")
    
    if failed_days:
        print(f"\n❌ Failed to process {len(failed_days)} days:")
        for day_data in failed_days:
            print(f"   - {day_data['date']}: {day_data['error']}")
    
    print("\n" + "="*70)
    
    return len(failed_days) == 0

def main():
    parser = argparse.ArgumentParser(description='Crawl historical news data')
    parser.add_argument(
        '--days',
        type=int,
        default=3,
        help='Number of days to go back (default: 3)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=30,
        help='Delay in seconds between processing each day (default: 30)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print what would be done without actually crawling'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No data will be crawled")
        print(f"Would process the following {args.days} days:")
        today = date.today()
        for i in range(1, args.days + 1):
            target_date = today - timedelta(days=i)
            print(f"   - {target_date}")
        print("\nTo actually run, remove the --dry-run flag")
        return
    
    # Validate days parameter
    if args.days < 1 or args.days > 30:
        print("Error: days must be between 1 and 30")
        sys.exit(1)
    
    # Run the async crawler
    start_time = time.time()
    success = asyncio.run(crawl_historical_data(args.days, args.delay))
    elapsed_time = time.time() - start_time
    
    print(f"\n⏱️  Total execution time: {elapsed_time:.1f} seconds")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()