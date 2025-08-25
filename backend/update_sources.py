#!/usr/bin/env python3
"""
Update production sources:
1. Remove specified sources
2. Update Anthropic Release Notes URL
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def update_sources():
    """Update sources in the database"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        sys.exit(1)
    
    client = create_client(url, key)
    
    # Sources to remove
    sources_to_remove = [
        'https://blog.google/technology/ai/',
        'https://news.ycombinator.com/',
        'https://www.reuters.com/technology/artificial-intelligence/',
        'https://simonwillison.net/',
        'https://www.anthropic.com/research'
    ]
    
    print("="*80)
    print("📝 UPDATING PRODUCTION SOURCES")
    print("="*80)
    
    # Step 1: Remove specified sources
    print("\n🗑️  Removing sources...")
    for source_url in sources_to_remove:
        try:
            # Delete by URL
            response = client.table('sources').delete().eq('url', source_url).execute()
            if response.data:
                print(f"  ✅ Removed: {source_url}")
            else:
                print(f"  ⚠️  Not found or already removed: {source_url}")
        except Exception as e:
            print(f"  ❌ Error removing {source_url}: {str(e)}")
    
    # Step 2: Update Anthropic Release Notes URL
    print("\n🔄 Updating Anthropic Release Notes URL...")
    old_url = 'https://docs.anthropic.com/en/release-notes/overview'
    new_url = 'https://docs.anthropic.com/en/release-notes/api'
    
    try:
        # Update the URL
        response = client.table('sources').update({
            'url': new_url
        }).eq('url', old_url).execute()
        
        if response.data:
            print(f"  ✅ Updated URL from:")
            print(f"     {old_url}")
            print(f"     to:")
            print(f"     {new_url}")
        else:
            print(f"  ⚠️  Anthropic Release Notes not found with old URL")
            # Try updating by name as fallback
            response = client.table('sources').update({
                'url': new_url
            }).eq('name', 'Anthropic Release Notes').execute()
            
            if response.data:
                print(f"  ✅ Updated by name to: {new_url}")
            else:
                print(f"  ❌ Could not find Anthropic Release Notes to update")
    except Exception as e:
        print(f"  ❌ Error updating URL: {str(e)}")
    
    # Step 3: List remaining active sources for verification
    print("\n" + "="*80)
    print("📊 UPDATED SOURCE LIST")
    print("="*80)
    
    try:
        response = client.table('sources').select('*').eq('active', True).order('source_type').order('name').execute()
        sources = response.data
        
        websites = [s for s in sources if s['source_type'] != 'twitter']
        twitter = [s for s in sources if s['source_type'] == 'twitter']
        
        print(f"\n✅ Active Sources: {len(sources)} total")
        print(f"   Websites: {len(websites)} | Twitter: {len(twitter)}")
        
        print("\n🌐 Website Sources:")
        for source in websites:
            print(f"  • {source['name']}: {source['url']}")
        
        print("\n🐦 Twitter Sources:")
        for source in twitter:
            username = source.get('twitter_username', 'N/A')
            print(f"  • {source['name']}: @{username}")
            
    except Exception as e:
        print(f"❌ Error fetching updated sources: {str(e)}")
    
    print("\n" + "="*80)
    print("✅ SOURCE UPDATE COMPLETE")
    print("="*80)

if __name__ == "__main__":
    update_sources()