#!/usr/bin/env python3
"""
Test script to verify Twitter integration
Run this after setting up your environment variables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports work correctly"""
    print("Testing imports...")
    try:
        from backend.src.services.twitter_service import TwitterService
        print("✓ TwitterService import OK")
        
        from backend.src.utils.twitter_utils import parse_twitter_input, validate_twitter_username
        print("✓ Twitter utils import OK")
        
        from backend.src.api.models.source import SourceType, SourceCreate
        print("✓ Source models import OK")
        
        from backend.src.services.openai_service import OpenAIService
        print("✓ OpenAI service import OK")
        
        from backend.src.services.supabase_client import SupabaseService
        print("✓ Supabase service import OK")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_url_parsing():
    """Test URL parsing functionality"""
    print("\nTesting URL parsing...")
    from backend.src.utils.twitter_utils import parse_twitter_input
    
    test_cases = [
        ('https://twitter.com/karpathy', 'karpathy', None),
        ('@sama', 'sama', None),
        ('ylecun:Yann LeCun', 'ylecun', 'Yann LeCun'),
        ('https://x.com/drjimfan', 'drjimfan', None),
        ('emollick', 'emollick', None),
    ]
    
    all_passed = True
    for input_str, expected_username, expected_name in test_cases:
        username, name = parse_twitter_input(input_str)
        if username == expected_username and name == expected_name:
            print(f"✓ {input_str:30} -> {username}")
        else:
            print(f"✗ {input_str:30} -> Expected: {expected_username}, Got: {username}")
            all_passed = False
    
    return all_passed

def test_env_vars():
    """Check if required environment variables are set"""
    print("\nChecking environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'OPENAI_API_KEY',
        'FIRECRAWL_API_KEY',
        'TWITTER_API_KEY'
    ]
    
    all_set = True
    for var in required_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is NOT set")
            all_set = False
    
    return all_set

def test_model_validation():
    """Test model validation"""
    print("\nTesting model validation...")
    from backend.src.api.models.source import SourceCreate, SourceType
    
    try:
        # Test Twitter source creation
        source = SourceCreate(
            name="Test Source",
            source_type=SourceType.TWITTER,
            twitter_input="https://twitter.com/testuser"
        )
        print(f"✓ Twitter source model validation OK")
        return True
    except Exception as e:
        print(f"✗ Model validation error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Twitter Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("URL Parsing", test_url_parsing()))
    results.append(("Environment Variables", test_env_vars()))
    results.append(("Model Validation", test_model_validation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("-" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n✅ All tests passed! Twitter integration is ready.")
        print("\nNext steps:")
        print("1. Run database migration:")
        print("   psql -d your_database -f backend/migrations/add_twitter_source_support.sql")
        print("2. Add Twitter sources:")
        print("   python scripts/manage_twitter_sources.py add-defaults")
        print("3. Test a source:")
        print("   python scripts/manage_twitter_sources.py test @karpathy")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        if not results[2][1]:  # Env vars test failed
            print("\nMake sure to set environment variables in .env file:")
            print("TWITTER_API_KEY=your-twitter-api-key")

if __name__ == "__main__":
    main()