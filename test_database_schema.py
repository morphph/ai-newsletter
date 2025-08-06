#!/usr/bin/env python3
"""
Test script to verify Supabase database schema matches requirements
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, date
import uuid

load_dotenv()

class DatabaseSchemaTest:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.client: Client = create_client(url, key)
        self.test_results = []
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        self.test_results.append((status, message))
    
    def test_sources_table(self):
        """Test sources table structure and operations"""
        self.log("Testing 'sources' table...")
        
        try:
            # Test SELECT
            response = self.client.table('sources').select('*').limit(1).execute()
            self.log("✓ Table 'sources' exists and is readable", "PASS")
            
            # Check columns
            if response.data and len(response.data) > 0:
                source = response.data[0]
                required_columns = ['id', 'name', 'url', 'active', 'created_at']
                optional_columns = ['category']
                
                for col in required_columns:
                    if col in source:
                        self.log(f"  ✓ Column '{col}' exists", "PASS")
                    else:
                        self.log(f"  ✗ Column '{col}' missing", "FAIL")
                
                for col in optional_columns:
                    if col in source:
                        self.log(f"  ✓ Optional column '{col}' exists", "PASS")
                    else:
                        self.log(f"  ○ Optional column '{col}' not present", "INFO")
            else:
                self.log("  ○ No data to verify columns (table is empty)", "WARN")
                
        except Exception as e:
            self.log(f"✗ Error testing sources table: {str(e)}", "FAIL")
            return False
        
        return True
    
    def test_articles_table(self):
        """Test articles table structure and operations"""
        self.log("Testing 'articles' table...")
        
        try:
            # Test SELECT
            response = self.client.table('articles').select('*').limit(1).execute()
            self.log("✓ Table 'articles' exists and is readable", "PASS")
            
            # Check columns
            if response.data and len(response.data) > 0:
                article = response.data[0]
                required_columns = [
                    'id', 'source_id', 'headline', 'url', 
                    'published_at', 'scraped_at', 'is_ai_related'
                ]
                optional_columns = [
                    'summary', 'full_content', 'tags', 'image_url',
                    'view_count', 'included_in_newsletter'
                ]
                
                for col in required_columns:
                    if col in article:
                        self.log(f"  ✓ Column '{col}' exists", "PASS")
                    else:
                        self.log(f"  ✗ Column '{col}' missing", "FAIL")
                
                for col in optional_columns:
                    if col in article:
                        self.log(f"  ✓ Optional column '{col}' exists", "PASS")
                    else:
                        self.log(f"  ○ Optional column '{col}' not present", "INFO")
            else:
                self.log("  ○ No data to verify columns (table is empty)", "WARN")
                
        except Exception as e:
            self.log(f"✗ Error testing articles table: {str(e)}", "FAIL")
            return False
        
        return True
    
    def test_relationships(self):
        """Test foreign key relationships"""
        self.log("Testing table relationships...")
        
        try:
            # Test articles with sources join
            response = self.client.table('articles').select(
                '*, sources!inner(name, category)'
            ).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                self.log("✓ Foreign key relationship articles.source_id -> sources.id works", "PASS")
            else:
                self.log("○ No data to test relationships", "WARN")
                
        except Exception as e:
            self.log(f"✗ Error testing relationships: {str(e)}", "FAIL")
            return False
        
        return True
    
    def test_crud_operations(self):
        """Test Create, Read, Update, Delete operations"""
        self.log("Testing CRUD operations...")
        
        test_source_id = None
        test_article_id = None
        
        try:
            # Create a test source
            test_source = {
                'name': 'Test Source ' + str(uuid.uuid4())[:8],
                'url': f'https://test-{uuid.uuid4()}.com',
                'category': 'Test Category',
                'active': False  # Set to false so it doesn't interfere with actual crawling
            }
            
            response = self.client.table('sources').insert(test_source).execute()
            if response.data:
                test_source_id = response.data[0]['id']
                self.log("✓ CREATE operation on 'sources' works", "PASS")
            else:
                self.log("✗ Failed to create test source", "FAIL")
                return False
            
            # Create a test article
            test_article = {
                'source_id': test_source_id,
                'headline': 'Test Article ' + str(uuid.uuid4())[:8],
                'url': f'https://test-article-{uuid.uuid4()}.com',
                'published_at': date.today().isoformat(),
                'is_ai_related': True,
                'summary': 'This is a test article summary'
            }
            
            response = self.client.table('articles').insert(test_article).execute()
            if response.data:
                test_article_id = response.data[0]['id']
                self.log("✓ CREATE operation on 'articles' works", "PASS")
            else:
                self.log("✗ Failed to create test article", "FAIL")
            
            # Test UPDATE
            update_data = {'summary': 'Updated test summary'}
            response = self.client.table('articles').update(update_data).eq('id', test_article_id).execute()
            if response.data:
                self.log("✓ UPDATE operation on 'articles' works", "PASS")
            
            # Test READ with filters
            response = self.client.table('articles').select('*').eq('id', test_article_id).execute()
            if response.data and response.data[0]['summary'] == 'Updated test summary':
                self.log("✓ READ operation with filters works", "PASS")
            
            # Clean up - DELETE test data
            self.client.table('articles').delete().eq('id', test_article_id).execute()
            self.client.table('sources').delete().eq('id', test_source_id).execute()
            self.log("✓ DELETE operations work (test data cleaned up)", "PASS")
            
        except Exception as e:
            self.log(f"✗ Error in CRUD operations: {str(e)}", "FAIL")
            # Try to clean up if possible
            if test_article_id:
                try:
                    self.client.table('articles').delete().eq('id', test_article_id).execute()
                except:
                    pass
            if test_source_id:
                try:
                    self.client.table('sources').delete().eq('id', test_source_id).execute()
                except:
                    pass
            return False
        
        return True
    
    def test_data_statistics(self):
        """Show current database statistics"""
        self.log("Database Statistics:")
        
        try:
            # Count sources
            sources = self.client.table('sources').select('*', count='exact').execute()
            active_sources = self.client.table('sources').select('*', count='exact').eq('active', True).execute()
            self.log(f"  Total sources: {sources.count}", "INFO")
            self.log(f"  Active sources: {active_sources.count}", "INFO")
            
            # Count articles
            articles = self.client.table('articles').select('*', count='exact').execute()
            ai_articles = self.client.table('articles').select('*', count='exact').eq('is_ai_related', True).execute()
            today_articles = self.client.table('articles').select('*', count='exact').eq('published_at', date.today()).execute()
            
            self.log(f"  Total articles: {articles.count}", "INFO")
            self.log(f"  AI-related articles: {ai_articles.count}", "INFO")
            self.log(f"  Today's articles: {today_articles.count}", "INFO")
            
            # Get categories
            categories = self.client.table('sources').select('category').execute()
            unique_categories = set(s['category'] for s in categories.data if s['category'])
            self.log(f"  Categories: {', '.join(unique_categories) if unique_categories else 'None'}", "INFO")
            
        except Exception as e:
            self.log(f"Error getting statistics: {str(e)}", "WARN")
    
    def run_all_tests(self):
        """Run all database tests"""
        print("\n" + "="*60)
        print("SUPABASE DATABASE SCHEMA TEST")
        print("="*60 + "\n")
        
        all_passed = True
        
        # Run tests
        all_passed &= self.test_sources_table()
        print()
        all_passed &= self.test_articles_table()
        print()
        all_passed &= self.test_relationships()
        print()
        all_passed &= self.test_crud_operations()
        print()
        self.test_data_statistics()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        pass_count = sum(1 for status, _ in self.test_results if status == "PASS")
        fail_count = sum(1 for status, _ in self.test_results if status == "FAIL")
        warn_count = sum(1 for status, _ in self.test_results if status == "WARN")
        
        print(f"✓ Passed: {pass_count}")
        print(f"✗ Failed: {fail_count}")
        print(f"⚠ Warnings: {warn_count}")
        
        if fail_count == 0:
            print("\n✅ All required database features are working correctly!")
            print("Your Supabase database is properly configured for the AI News App.")
        else:
            print("\n❌ Some tests failed. Please check your database schema.")
            print("You may need to run the migration SQL in your Supabase dashboard.")
        
        return all_passed

if __name__ == "__main__":
    try:
        tester = DatabaseSchemaTest()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Please check your environment variables and database connection.")
        sys.exit(1)