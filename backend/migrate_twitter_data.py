#!/usr/bin/env python3
"""
Migrate remaining Twitter data from articles to tweets table
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class TwitterDataMigrator:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.client: Client = create_client(url, key)
        self.migrated_count = 0
        self.failed_count = 0
    
    def get_twitter_articles(self):
        """Get Twitter items still in articles table"""
        try:
            response = self.client.table('articles').select(
                '*, sources!inner(name, source_type, twitter_username)'
            ).not_.is_('tweet_id', 'null').execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching Twitter articles: {e}")
            return []
    
    def migrate_to_tweets_table(self, article):
        """Migrate a single article to tweets table"""
        try:
            # Prepare tweet data
            tweet_data = {
                'source_id': article['source_id'],
                'tweet_id': article['tweet_id'],
                'author_username': article.get('author_username', 
                                              article.get('sources', {}).get('twitter_username', 'unknown')),
                'content': article.get('full_content') or article.get('headline', ''),
                'like_count': article.get('like_count', 0),
                'retweet_count': article.get('retweet_count', 0),
                'reply_count': article.get('reply_count', 0),
                'is_ai_related': article.get('is_ai_related', False),
                'ai_summary': article.get('summary'),
                'ai_tags': article.get('tags', []),
                'published_at': article['published_at'],
                'fetched_at': article.get('scraped_at', datetime.now().isoformat()),
                'included_in_newsletter': article.get('included_in_newsletter', False)
            }
            
            # Check if tweet already exists
            existing = self.client.table('tweets').select('id').eq('tweet_id', article['tweet_id']).execute()
            
            if existing.data and len(existing.data) > 0:
                logger.info(f"Tweet {article['tweet_id']} already exists, updating...")
                # Update existing tweet
                response = self.client.table('tweets').update({
                    'like_count': tweet_data['like_count'],
                    'retweet_count': tweet_data['retweet_count'],
                    'reply_count': tweet_data['reply_count'],
                    'updated_at': datetime.now().isoformat()
                }).eq('tweet_id', article['tweet_id']).execute()
            else:
                logger.info(f"Migrating new tweet {article['tweet_id']}...")
                # Insert new tweet
                response = self.client.table('tweets').insert(tweet_data).execute()
            
            if response.data:
                self.migrated_count += 1
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error migrating tweet {article.get('tweet_id')}: {e}")
            self.failed_count += 1
            return False
    
    def delete_migrated_article(self, article_id):
        """Delete the migrated article from articles table"""
        try:
            response = self.client.table('articles').delete().eq('id', article_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            return False
    
    def run_migration(self, delete_after_migration=False):
        """Run the complete migration"""
        logger.info("=" * 60)
        logger.info("STARTING TWITTER DATA MIGRATION")
        logger.info("=" * 60)
        
        # Get Twitter articles
        twitter_articles = self.get_twitter_articles()
        
        if not twitter_articles:
            logger.info("✅ No Twitter data found in articles table!")
            return True
        
        logger.info(f"Found {len(twitter_articles)} Twitter items to migrate")
        
        # Migrate each article
        successfully_migrated = []
        for article in twitter_articles:
            source_name = article.get('sources', {}).get('name', 'Unknown')
            logger.info(f"\nMigrating: {source_name} - {article.get('headline', '')[:50]}...")
            
            if self.migrate_to_tweets_table(article):
                successfully_migrated.append(article['id'])
                logger.info(f"✅ Successfully migrated")
            else:
                logger.error(f"❌ Failed to migrate")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total items: {len(twitter_articles)}")
        logger.info(f"Successfully migrated: {self.migrated_count}")
        logger.info(f"Failed: {self.failed_count}")
        
        # Optionally delete migrated articles
        if delete_after_migration and successfully_migrated:
            logger.info("\n" + "=" * 60)
            logger.info("CLEANUP: Removing migrated items from articles table")
            logger.info("=" * 60)
            
            deleted_count = 0
            for article_id in successfully_migrated:
                if self.delete_migrated_article(article_id):
                    deleted_count += 1
                    logger.info(f"✅ Deleted article {article_id}")
                else:
                    logger.error(f"❌ Failed to delete article {article_id}")
            
            logger.info(f"\nDeleted {deleted_count}/{len(successfully_migrated)} migrated articles")
        
        return self.failed_count == 0
    
    def verify_migration(self):
        """Verify the migration was successful"""
        logger.info("\n" + "=" * 60)
        logger.info("VERIFYING MIGRATION")
        logger.info("=" * 60)
        
        # Check articles table
        articles_response = self.client.table('articles').select('count', count='exact').not_.is_('tweet_id', 'null').execute()
        articles_with_tweets = articles_response.count if articles_response.count else 0
        
        # Check tweets table
        tweets_response = self.client.table('tweets').select('count', count='exact').execute()
        total_tweets = tweets_response.count if tweets_response.count else 0
        
        logger.info(f"Articles with tweet_id still in articles table: {articles_with_tweets}")
        logger.info(f"Total tweets in tweets table: {total_tweets}")
        
        if articles_with_tweets == 0:
            logger.info("✅ All Twitter data successfully migrated!")
        else:
            logger.warning(f"⚠️  {articles_with_tweets} Twitter items still in articles table")
        
        return articles_with_tweets == 0

def main():
    """Main execution"""
    try:
        migrator = TwitterDataMigrator()
        
        # Ask user if they want to delete after migration
        print("\n" + "=" * 60)
        print("TWITTER DATA MIGRATION TOOL")
        print("=" * 60)
        print("\nThis tool will migrate Twitter data from articles to tweets table.")
        print("\nOptions:")
        print("1. Migrate only (keep originals in articles table)")
        print("2. Migrate and delete originals")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '3':
            print("Exiting...")
            return 0
        
        delete_after = (choice == '2')
        
        # Run migration
        success = migrator.run_migration(delete_after_migration=delete_after)
        
        # Verify
        migrator.verify_migration()
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())