#!/usr/bin/env python3
"""
Add text-to-video foundation model sources to production database
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from uuid import uuid4

# Load environment variables
load_dotenv()

def add_video_sources():
    """Add text-to-video sources to the database"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        sys.exit(1)
    
    client = create_client(url, key)
    
    # Define sources to add (excluding Pika and Haiper as requested)
    sources_to_add = [
        # Website sources
        {
            'id': str(uuid4()),
            'name': 'Runway Research',
            'url': 'https://runwayml.com/research/',
            'source_type': 'website',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': 'Stability AI News',
            'url': 'https://stability.ai/news',
            'source_type': 'website',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': 'Meta AI Blog',
            'url': 'https://ai.meta.com/blog/',
            'source_type': 'website',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': 'Google Research Blog',
            'url': 'https://research.google/blog/',
            'source_type': 'website',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': 'Genmo Blog',
            'url': 'https://www.genmo.ai/blog',
            'source_type': 'website',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': 'HeyGen Blog',
            'url': 'https://www.heygen.com/blog',
            'source_type': 'website',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': 'Synthesia News',
            'url': 'https://www.synthesia.io/blog/category/synthesia-news',
            'source_type': 'website',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': 'Higgsfield Posts',
            'url': 'https://higgsfield.ai/posts',
            'source_type': 'website',
            'active': True
        },
        
        # Twitter sources
        {
            'id': str(uuid4()),
            'name': '@runwayml',
            'url': 'https://twitter.com/runwayml',
            'twitter_username': 'runwayml',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@StabilityAI',
            'url': 'https://twitter.com/StabilityAI',
            'twitter_username': 'StabilityAI',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@MetaAI',
            'url': 'https://twitter.com/MetaAI',
            'twitter_username': 'MetaAI',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@GoogleAI',
            'url': 'https://twitter.com/GoogleAI',
            'twitter_username': 'GoogleAI',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@GoogleDeepMind',
            'url': 'https://twitter.com/GoogleDeepMind',
            'twitter_username': 'GoogleDeepMind',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@OpenAI',
            'url': 'https://twitter.com/OpenAI',
            'twitter_username': 'OpenAI',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@genmoai',
            'url': 'https://twitter.com/genmoai',
            'twitter_username': 'genmoai',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@HeyGen_Official',
            'url': 'https://twitter.com/HeyGen_Official',
            'twitter_username': 'HeyGen_Official',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@synthesiaIO',
            'url': 'https://twitter.com/synthesiaIO',
            'twitter_username': 'synthesiaIO',
            'source_type': 'twitter',
            'active': True
        },
        {
            'id': str(uuid4()),
            'name': '@higgsfield_ai',
            'url': 'https://twitter.com/higgsfield_ai',
            'twitter_username': 'higgsfield_ai',
            'source_type': 'twitter',
            'active': True
        }
    ]
    
    print("="*80)
    print("🎬 ADDING TEXT-TO-VIDEO SOURCES")
    print("="*80)
    
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    for source in sources_to_add:
        try:
            # Check if source already exists (by URL or twitter_username)
            if source['source_type'] == 'twitter':
                existing = client.table('sources').select('*').eq('twitter_username', source['twitter_username']).execute()
            else:
                existing = client.table('sources').select('*').eq('url', source['url']).execute()
            
            if existing.data:
                print(f"  ⚠️  Already exists: {source['name']}")
                skipped_count += 1
            else:
                # Add the source
                response = client.table('sources').insert(source).execute()
                if response.data:
                    icon = "🐦" if source['source_type'] == 'twitter' else "🌐"
                    print(f"  ✅ Added {icon} {source['name']}")
                    added_count += 1
                else:
                    print(f"  ❌ Failed to add: {source['name']}")
                    error_count += 1
                    
        except Exception as e:
            print(f"  ❌ Error adding {source['name']}: {str(e)}")
            error_count += 1
    
    # Print summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"✅ Added: {added_count} sources")
    print(f"⚠️  Skipped (already exist): {skipped_count} sources")
    if error_count > 0:
        print(f"❌ Errors: {error_count} sources")
    
    # List all active sources
    print("\n" + "="*80)
    print("📋 ALL ACTIVE SOURCES")
    print("="*80)
    
    try:
        response = client.table('sources').select('*').eq('active', True).order('source_type').order('name').execute()
        sources = response.data
        
        websites = [s for s in sources if s['source_type'] != 'twitter']
        twitter = [s for s in sources if s['source_type'] == 'twitter']
        
        print(f"\n✅ Total Active Sources: {len(sources)}")
        print(f"   Websites: {len(websites)} | Twitter: {len(twitter)}")
        
        print("\n🌐 Website Sources:")
        for source in websites:
            print(f"  • {source['name']}: {source['url']}")
        
        print("\n🐦 Twitter Sources:")
        for source in twitter:
            username = source.get('twitter_username', 'N/A')
            print(f"  • @{username}")
            
    except Exception as e:
        print(f"❌ Error fetching sources: {str(e)}")
    
    print("\n" + "="*80)
    print("✅ VIDEO SOURCES UPDATE COMPLETE")
    print("="*80)

if __name__ == "__main__":
    add_video_sources()