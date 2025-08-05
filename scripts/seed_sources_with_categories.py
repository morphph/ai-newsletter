import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.supabase_client import SupabaseService

async def seed_sources_with_categories():
    supabase = SupabaseService()
    
    # Categorized sources
    sources = [
        # Official AI Companies
        {
            'name': 'OpenAI News',
            'url': 'https://openai.com/news/',
            'category': 'Official AI Companies',
            'active': True
        },
        {
            'name': 'Anthropic News',
            'url': 'https://www.anthropic.com/news',
            'category': 'Official AI Companies',
            'active': True
        },
        {
            'name': 'Anthropic Release Notes',
            'url': 'https://docs.anthropic.com/en/release-notes/overview',
            'category': 'Official AI Companies',
            'active': True
        },
        {
            'name': 'Anthropic Research',
            'url': 'https://www.anthropic.com/research',
            'category': 'Official AI Companies',
            'active': True
        },
        {
            'name': 'Google AI Blog',
            'url': 'https://blog.google/technology/ai/',
            'category': 'Official AI Companies',
            'active': True
        },
        {
            'name': 'Google Developers Blog',
            'url': 'https://blog.google/technology/developers/',
            'category': 'Official AI Companies',
            'active': True
        },
        {
            'name': 'Google DeepMind Blog',
            'url': 'https://blog.google/technology/google-deepmind/',
            'category': 'Official AI Companies',
            'active': True
        },
        {
            'name': 'Google Gemini Developer Blog',
            'url': 'https://developers.googleblog.com/en/search/?product_categories=Gemini',
            'category': 'Official AI Companies',
            'active': True
        },
        
        # AI Researchers & Thought Leaders
        {
            'name': 'Simon Willison',
            'url': 'https://simonwillison.net/',
            'category': 'AI Researchers & Thought Leaders',
            'active': True
        },
        {
            'name': 'Hacker News',
            'url': 'https://news.ycombinator.com/',
            'category': 'AI Researchers & Thought Leaders',
            'active': True
        },
        {
            'name': 'Reuters AI News',
            'url': 'https://www.reuters.com/technology/artificial-intelligence/',
            'category': 'AI Researchers & Thought Leaders',
            'active': True
        },
        
        # AI Tools
        {
            'name': 'Firecrawl Blog',
            'url': 'https://www.firecrawl.dev/blog/',
            'category': 'AI Tools',
            'active': True
        }
    ]
    
    print("Seeding news sources with categories...")
    print("\nNote: Since we can't add the category column via API, you'll need to:")
    print("1. Add the category column to your sources table in Supabase")
    print("2. Run this script to populate sources with categories")
    print("\nAlternatively, run this SQL in Supabase SQL Editor:")
    print("ALTER TABLE sources ADD COLUMN IF NOT EXISTS category text;")
    print("\n" + "="*60 + "\n")
    
    # Try to seed sources
    for source in sources:
        try:
            existing = supabase.client.table('sources').select('*').eq('url', source['url']).execute()
            
            if existing.data:
                print(f"Source already exists: {source['name']} ({source['category']})")
                # Try to update with category if column exists
                try:
                    supabase.client.table('sources').update({
                        'category': source['category']
                    }).eq('url', source['url']).execute()
                    print(f"  ✓ Updated category")
                except:
                    print(f"  ⚠ Could not update category (column may not exist)")
            else:
                result = supabase.client.table('sources').insert(source).execute()
                if result.data:
                    print(f"✓ Added source: {source['name']} ({source['category']})")
                else:
                    print(f"✗ Failed to add source: {source['name']}")
        except Exception as e:
            print(f"Error with source {source['name']}: {e}")
    
    print("\n" + "="*60)
    print("\nSeeding completed!")
    
    # Display sources by category
    print("\nSources by category:")
    all_sources = supabase.client.table('sources').select('*').execute()
    
    # Group by category (if available)
    categories = {}
    for src in all_sources.data:
        cat = src.get('category', 'Uncategorized')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(src)
    
    for category, sources_list in sorted(categories.items()):
        print(f"\n{category}:")
        for src in sorted(sources_list, key=lambda x: x['name']):
            print(f"  - {src['name']} ({src['url']})")
    
    print(f"\nTotal sources: {len(all_sources.data)}")

if __name__ == "__main__":
    asyncio.run(seed_sources_with_categories())