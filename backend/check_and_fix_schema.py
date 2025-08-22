#!/usr/bin/env python3
"""
Database Schema Checker and Fixer
Checks current Supabase schema and applies missing migrations
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

class SchemaChecker:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.client: Client = create_client(url, key)
        self.issues = []
        self.fixes_applied = []
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            # Try to select from the table
            response = self.client.table(table_name).select('*').limit(1).execute()
            return True
        except Exception as e:
            if 'relation' in str(e) and 'does not exist' in str(e):
                return False
            # Some other error occurred
            logger.error(f"Error checking table {table_name}: {e}")
            return False
    
    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            # Try to select the specific column
            response = self.client.table(table_name).select(column_name).limit(1).execute()
            return True
        except Exception as e:
            if 'column' in str(e).lower() and 'does not exist' in str(e).lower():
                return False
            return False
    
    def run_checks(self):
        """Run all schema checks"""
        logger.info("=" * 60)
        logger.info("STARTING DATABASE SCHEMA CHECKS")
        logger.info("=" * 60)
        
        # Check core tables
        logger.info("\n1. Checking Core Tables:")
        tables_to_check = ['sources', 'articles', 'tweets', 'source_stats']
        
        for table in tables_to_check:
            exists = self.check_table_exists(table)
            status = "✅ EXISTS" if exists else "❌ MISSING"
            logger.info(f"   {table}: {status}")
            if not exists:
                self.issues.append(f"Table '{table}' is missing")
        
        # Check sources table columns
        logger.info("\n2. Checking 'sources' table columns:")
        if self.check_table_exists('sources'):
            source_columns = {
                'id': 'Core column',
                'name': 'Core column',
                'url': 'Core column',
                'source_type': 'For Twitter/Website distinction',
                'twitter_username': 'For Twitter sources',
                'active': 'Source status',
                'category': 'Content category'
            }
            
            for col, description in source_columns.items():
                exists = self.check_column_exists('sources', col)
                status = "✅" if exists else "❌"
                logger.info(f"   {col}: {status} - {description}")
                if not exists:
                    self.issues.append(f"Column 'sources.{col}' is missing")
        
        # Check articles table columns
        logger.info("\n3. Checking 'articles' table columns:")
        if self.check_table_exists('articles'):
            article_columns = {
                'processing_stage': 'Pipeline tracking',
                'crawl_batch_id': 'Batch processing',
                'actual_published_date': 'Accurate date tracking',
                'tweet_id': 'Legacy Twitter support',
                'author_username': 'Legacy Twitter author',
                'like_count': 'Legacy engagement',
                'retweet_count': 'Legacy engagement',
                'reply_count': 'Legacy engagement'
            }
            
            for col, description in article_columns.items():
                exists = self.check_column_exists('articles', col)
                status = "✅" if exists else "❌"
                logger.info(f"   {col}: {status} - {description}")
                if not exists and col in ['processing_stage', 'crawl_batch_id', 'actual_published_date']:
                    self.issues.append(f"Column 'articles.{col}' is missing")
        
        # Check tweets table structure
        logger.info("\n4. Checking 'tweets' table structure:")
        if self.check_table_exists('tweets'):
            logger.info("   ✅ Tweets table exists")
            
            # Check key columns
            tweet_columns = ['tweet_id', 'author_username', 'content', 'is_ai_related', 
                           'published_at', 'like_count', 'retweet_count']
            for col in tweet_columns:
                exists = self.check_column_exists('tweets', col)
                if not exists:
                    logger.info(f"   ❌ Missing column: {col}")
                    self.issues.append(f"Column 'tweets.{col}' is missing")
        else:
            logger.info("   ❌ Tweets table does not exist")
            self.issues.append("Tweets table needs to be created")
        
        # Check for Twitter data in articles table
        logger.info("\n5. Checking for Twitter data in articles table:")
        try:
            response = self.client.table('articles').select('count', count='exact').not_.is_('tweet_id', 'null').execute()
            twitter_count = response.count if response.count else 0
            
            if twitter_count > 0:
                logger.info(f"   ⚠️  Found {twitter_count} Twitter items in articles table")
                logger.info(f"   These need to be migrated to tweets table")
                self.issues.append(f"{twitter_count} Twitter items need migration from articles to tweets table")
            else:
                logger.info("   ✅ No Twitter data in articles table")
        except Exception as e:
            logger.error(f"   Error checking Twitter data: {e}")
        
        # Check views
        logger.info("\n6. Checking database views:")
        views_to_check = ['unified_content', 'article_processing_status', 'daily_twitter_stats']
        
        for view in views_to_check:
            # Views behave like tables for selection
            exists = self.check_table_exists(view)
            status = "✅ EXISTS" if exists else "❌ MISSING"
            logger.info(f"   {view}: {status}")
            if not exists and view == 'unified_content':
                self.issues.append(f"View '{view}' is missing - critical for API")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("SCHEMA CHECK SUMMARY")
        logger.info("=" * 60)
        
        if not self.issues:
            logger.info("✅ All schema checks passed! Database is properly configured.")
        else:
            logger.warning(f"⚠️  Found {len(self.issues)} issues:")
            for i, issue in enumerate(self.issues, 1):
                logger.warning(f"   {i}. {issue}")
        
        return len(self.issues) == 0
    
    def generate_fix_script(self):
        """Generate SQL script to fix identified issues"""
        if not self.issues:
            logger.info("No issues to fix!")
            return None
        
        logger.info("\n" + "=" * 60)
        logger.info("GENERATING FIX SCRIPT")
        logger.info("=" * 60)
        
        fix_script = []
        fix_script.append("-- Auto-generated fix script for schema issues")
        fix_script.append(f"-- Generated at: {datetime.now().isoformat()}")
        fix_script.append("-- REVIEW CAREFULLY BEFORE RUNNING IN PRODUCTION\n")
        
        # Check which migrations need to be applied
        needs_twitter_support = any('source_type' in issue or 'twitter_username' in issue for issue in self.issues)
        needs_tweets_table = any('tweets' in issue.lower() for issue in self.issues)
        needs_processing_stages = any('processing_stage' in issue for issue in self.issues)
        
        if needs_twitter_support:
            logger.info("📝 Adding Twitter source support migration")
            fix_script.append("\n-- Migration 1: Add Twitter Source Support")
            fix_script.append("-- From: add_twitter_source_support.sql")
            with open('/Users/bytedance/Desktop/test_ainews_0804/backend/migrations/add_twitter_source_support.sql', 'r') as f:
                fix_script.append(f.read())
        
        if needs_tweets_table:
            logger.info("📝 Adding separate Twitter content migration")
            fix_script.append("\n-- Migration 2: Separate Twitter Content")
            fix_script.append("-- From: separate_twitter_content.sql")
            with open('/Users/bytedance/Desktop/test_ainews_0804/backend/migrations/separate_twitter_content.sql', 'r') as f:
                fix_script.append(f.read())
        
        if needs_processing_stages:
            logger.info("📝 Adding processing stages migration")
            fix_script.append("\n-- Migration 3: Add Processing Stages")
            fix_script.append("-- From: add_processing_stages.sql")
            with open('/Users/bytedance/Desktop/test_ainews_0804/backend/migrations/add_processing_stages.sql', 'r') as f:
                fix_script.append(f.read())
        
        # Save fix script
        fix_script_path = '/Users/bytedance/Desktop/test_ainews_0804/backend/fix_schema.sql'
        with open(fix_script_path, 'w') as f:
            f.write('\n'.join(fix_script))
        
        logger.info(f"\n✅ Fix script saved to: {fix_script_path}")
        logger.info("\nTo apply fixes:")
        logger.info("1. Review the script carefully")
        logger.info("2. Run in Supabase SQL Editor")
        logger.info("3. Or run: python apply_migrations.py")
        
        return fix_script_path
    
    def check_data_integrity(self):
        """Check data integrity after migrations"""
        logger.info("\n" + "=" * 60)
        logger.info("DATA INTEGRITY CHECKS")
        logger.info("=" * 60)
        
        # Check for orphaned records
        logger.info("\n1. Checking for orphaned articles:")
        try:
            response = self.client.table('articles').select('count', count='exact').is_('source_id', 'null').execute()
            orphaned = response.count if response.count else 0
            if orphaned > 0:
                logger.warning(f"   ⚠️  Found {orphaned} orphaned articles")
            else:
                logger.info("   ✅ No orphaned articles")
        except Exception as e:
            logger.error(f"   Error checking orphaned articles: {e}")
        
        # Check source types
        logger.info("\n2. Checking source types:")
        try:
            response = self.client.table('sources').select('source_type, count', count='exact').execute()
            logger.info(f"   Total sources: {len(response.data) if response.data else 0}")
            
            # Count by type
            if response.data:
                website_count = sum(1 for s in response.data if s.get('source_type') == 'website')
                twitter_count = sum(1 for s in response.data if s.get('source_type') == 'twitter')
                unknown_count = len(response.data) - website_count - twitter_count
                
                logger.info(f"   Website sources: {website_count}")
                logger.info(f"   Twitter sources: {twitter_count}")
                if unknown_count > 0:
                    logger.warning(f"   ⚠️  Unknown type: {unknown_count}")
        except Exception as e:
            logger.error(f"   Error checking source types: {e}")
        
        # Check date consistency
        logger.info("\n3. Checking date consistency:")
        try:
            # Check for future dates
            response = self.client.table('articles').select('count', count='exact').gt('published_at', datetime.now().isoformat()).execute()
            future_articles = response.count if response.count else 0
            
            if future_articles > 0:
                logger.warning(f"   ⚠️  Found {future_articles} articles with future dates")
            else:
                logger.info("   ✅ No articles with future dates")
        except Exception as e:
            logger.error(f"   Error checking dates: {e}")

def main():
    """Main execution"""
    try:
        checker = SchemaChecker()
        
        # Run checks
        all_good = checker.run_checks()
        
        if not all_good:
            # Generate fix script
            fix_script = checker.generate_fix_script()
            
            # Ask user if they want to see data integrity checks
            logger.info("\nWould you like to run data integrity checks? (Recommended)")
            logger.info("This will check for orphaned records and data consistency.")
        
        # Always run integrity checks
        checker.check_data_integrity()
        
        logger.info("\n" + "=" * 60)
        logger.info("SCHEMA CHECK COMPLETE")
        logger.info("=" * 60)
        
        if all_good:
            logger.info("✅ Your database schema is properly configured!")
        else:
            logger.info("⚠️  Schema issues detected. Please review the fix script.")
            logger.info("After applying fixes, run this script again to verify.")
        
        return 0 if all_good else 1
        
    except Exception as e:
        logger.error(f"Error running schema checker: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())