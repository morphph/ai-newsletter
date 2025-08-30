#!/usr/bin/env python3
"""
Test script to verify news crawler configuration and functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    print("=" * 60)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    required_vars = {
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_KEY': 'Supabase anon/service key',
        'OPENAI_API_KEY': 'OpenAI API key for GPT-4',
        'FIRECRAWL_API_KEY': 'Firecrawl API key for web scraping'
    }
    
    missing_vars = []
    found_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✓ {var}: {masked_value} ({description})")
            found_vars.append(var)
        else:
            print(f"✗ {var}: NOT SET ({description})")
            missing_vars.append(var)
    
    print("\nSummary:")
    print(f"  Found: {len(found_vars)}/{len(required_vars)} variables")
    
    if missing_vars:
        print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
        print("\nTo fix this:")
        print("1. Copy .env.example to .env")
        print("2. Fill in the missing values in .env")
        return False
    
    print("\n✅ All environment variables are set!")
    return True

def test_imports():
    """Test if all required modules can be imported"""
    print("\n" + "=" * 60)
    print("TESTING MODULE IMPORTS")
    print("=" * 60)
    
    modules_to_test = [
        ('supabase', 'Supabase client library'),
        ('openai', 'OpenAI API library'),
        ('firecrawl', 'Firecrawl web scraping'),
        ('aiohttp', 'Async HTTP client'),
        ('bs4', 'BeautifulSoup for HTML parsing'),
        ('fastapi', 'FastAPI framework'),
        ('pydantic', 'Data validation'),
    ]
    
    failed_imports = []
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name}: {description}")
        except ImportError as e:
            print(f"✗ {module_name}: FAILED ({description})")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n⚠️  Failed imports: {', '.join(failed_imports)}")
        print("\nTo fix this, run:")
        print("  pip install -r backend/requirements.txt")
        return False
    
    print("\n✅ All required modules can be imported!")
    return True

def test_database_connection():
    """Test Supabase database connection"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        # Add backend to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from src.services.supabase_client import SupabaseService
        
        print("Connecting to Supabase...")
        supabase = SupabaseService()
        
        # Test query
        print("Testing database query...")
        result = supabase.client.table('sources').select('id, name, source_type').limit(5).execute()
        
        print(f"✓ Database connection successful!")
        print(f"  Found {len(result.data)} sources in database")
        
        if result.data:
            print("\n  Sample sources:")
            for source in result.data[:3]:
                print(f"    - {source['name']} ({source['source_type']})")
        
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nPossible issues:")
        print("  1. Check SUPABASE_URL and SUPABASE_KEY are correct")
        print("  2. Verify your Supabase project is active")
        print("  3. Check network connectivity")
        return False

def test_crawler_import():
    """Test if the crawler can be imported"""
    print("\n" + "=" * 60)
    print("TESTING CRAWLER MODULE")
    print("=" * 60)
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from src.workers.news_crawler_v3 import EnhancedNewsCrawlerV3
        
        print("✓ Crawler module imported successfully!")
        
        # Try to instantiate
        print("Testing crawler instantiation...")
        crawler = EnhancedNewsCrawlerV3()
        print("✓ Crawler instantiated successfully!")
        
        return True
        
    except Exception as e:
        print(f"✗ Crawler import failed: {e}")
        print("\nThis might be due to:")
        print("  1. Missing dependencies")
        print("  2. Import path issues")
        print("  3. Syntax errors in the crawler code")
        return False

def test_minimal_crawl():
    """Run a minimal crawl test"""
    print("\n" + "=" * 60)
    print("TESTING MINIMAL CRAWL (DRY RUN)")
    print("=" * 60)
    
    try:
        import asyncio
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from src.workers.news_crawler_v3 import EnhancedNewsCrawlerV3
        
        async def run_test():
            crawler = EnhancedNewsCrawlerV3()
            
            # Get active sources
            sources = crawler.supabase.get_active_sources()
            print(f"Found {len(sources)} active sources")
            
            if sources:
                print(f"\nTesting with first source: {sources[0]['name']}")
                print("(Not actually crawling, just checking setup)")
                
            return True
        
        result = asyncio.run(run_test())
        print("\n✅ Crawler setup test passed!")
        return result
        
    except Exception as e:
        print(f"✗ Crawler test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n🔍 NEWS CRAWLER DIAGNOSTIC TEST")
    print("================================\n")
    
    all_passed = True
    
    # Run tests in order
    tests = [
        ("Environment Variables", check_environment),
        ("Python Modules", test_imports),
        ("Database Connection", test_database_connection),
        ("Crawler Module", test_crawler_import),
        ("Minimal Crawl Test", test_minimal_crawl),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
            all_passed = all_passed and results[test_name]
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    if all_passed:
        print("\n🎉 All tests passed! Your crawler should work.")
        print("\nNext steps:")
        print("1. Push the fixed workflow file to GitHub")
        print("2. Ensure GitHub secrets are set")
        print("3. Trigger the workflow manually to test")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nFor GitHub Actions to work, you need:")
        print("1. All environment variables set as GitHub secrets")
        print("2. All Python dependencies available")
        print("3. Proper database access")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())