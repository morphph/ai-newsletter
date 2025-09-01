#!/usr/bin/env python3
"""
Backfill missing articles from August 21-30, 2024
"""

import asyncio
import sys
import os
from datetime import date

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.workers.news_crawler_v3 import EnhancedNewsCrawlerV3

async def backfill_dates():
    """Backfill specific dates from August 2025"""
    dates_to_backfill = [
        date(2025, 8, 21),
        date(2025, 8, 22),
        date(2025, 8, 23),
        date(2025, 8, 24),
        date(2025, 8, 25),
        date(2025, 8, 26),
        date(2025, 8, 27),
        date(2025, 8, 28),
        date(2025, 8, 29),
        date(2025, 8, 30),
        date(2025, 8, 31),
    ]
    
    print("\n" + "="*70)
    print("AUGUST 2025 BACKFILL - Processing missing dates")
    print("="*70)
    
    successful_dates = []
    failed_dates = []
    
    for target_date in dates_to_backfill:
        print(f"\n📅 Processing {target_date}...")
        print("-" * 50)
        
        try:
            # Create a new crawler instance for each date
            crawler = EnhancedNewsCrawlerV3()
            
            # Run the pipeline for this specific date
            results = await crawler.run_full_pipeline(target_date)
            
            tweets_count = len(results.get('tweets', []))
            articles_count = len(results.get('articles', []))
            
            print(f"✅ Successfully processed {target_date}")
            print(f"   - {tweets_count} AI-relevant tweets")
            print(f"   - {articles_count} AI-relevant articles")
            
            successful_dates.append({
                'date': target_date,
                'tweets': tweets_count,
                'articles': articles_count
            })
            
            # Add small delay between dates to avoid rate limiting
            if target_date != dates_to_backfill[-1]:
                print(f"\n⏳ Waiting 5 seconds before next date...")
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"❌ Failed to process {target_date}: {str(e)}")
            failed_dates.append({
                'date': target_date,
                'error': str(e)
            })
            continue
    
    # Print final summary
    print("\n" + "="*70)
    print("BACKFILL SUMMARY")
    print("="*70)
    
    if successful_dates:
        print(f"\n✅ Successfully processed {len(successful_dates)} dates:")
        total_tweets = 0
        total_articles = 0
        for day_data in successful_dates:
            print(f"   - {day_data['date']}: {day_data['tweets']} tweets, {day_data['articles']} articles")
            total_tweets += day_data['tweets']
            total_articles += day_data['articles']
        print(f"\n   Total: {total_tweets} tweets, {total_articles} articles")
    
    if failed_dates:
        print(f"\n❌ Failed to process {len(failed_dates)} dates:")
        for day_data in failed_dates:
            print(f"   - {day_data['date']}: {day_data['error']}")
    
    print("\n" + "="*70)
    
    return len(failed_dates) == 0

if __name__ == "__main__":
    success = asyncio.run(backfill_dates())
    sys.exit(0 if success else 1)