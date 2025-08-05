import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.supabase_client import SupabaseService

async def seed_sources():
    supabase = SupabaseService()
    
    sources = [
        {
            'name': 'Firecrawl Blog',
            'url': 'https://www.firecrawl.dev/blog/',
            'active': True
        },
        {
            'name': 'OpenAI News',
            'url': 'https://openai.com/news/',
            'active': True
        },
        {
            'name': 'Anthropic News',
            'url': 'https://www.anthropic.com/news',
            'active': True
        },
        {
            'name': 'Anthropic Release Notes',
            'url': 'https://docs.anthropic.com/en/release-notes/overview',
            'active': True
        },
        {
            'name': 'Google AI Blog',
            'url': 'https://blog.google/technology/ai/',
            'active': True
        },
        {
            'name': 'Google Developers Blog',
            'url': 'https://blog.google/technology/developers/',
            'active': True
        },
        {
            'name': 'Google DeepMind Blog',
            'url': 'https://blog.google/technology/google-deepmind/',
            'active': True
        },
        {
            'name': 'Google Gemini Developer Blog',
            'url': 'https://developers.googleblog.com/en/search/?product_categories=Gemini',
            'active': True
        },
        {
            'name': 'Hacker News',
            'url': 'https://news.ycombinator.com/',
            'active': True
        },
        {
            'name': 'Reuters AI News',
            'url': 'https://www.reuters.com/technology/artificial-intelligence/',
            'active': True
        },
        {
            'name': 'Simon Willison',
            'url': 'https://simonwillison.net/',
            'active': True
        },
        {
            'name': 'AI News by Buttondown',
            'url': 'https://buttondown.email/ainews/archive/',
            'active': True
        }
    ]
    
    print("Seeding news sources...")
    
    for source in sources:
        try:
            existing = supabase.client.table('sources').select('*').eq('url', source['url']).execute()
            
            if existing.data:
                print(f"Source already exists: {source['name']}")
            else:
                result = supabase.client.table('sources').insert(source).execute()
                if result.data:
                    print(f"Added source: {source['name']}")
                else:
                    print(f"Failed to add source: {source['name']}")
        except Exception as e:
            print(f"Error adding source {source['name']}: {e}")
    
    print("\nSeeding completed!")
    
    all_sources = supabase.client.table('sources').select('*').execute()
    print(f"\nTotal sources in database: {len(all_sources.data)}")

if __name__ == "__main__":
    asyncio.run(seed_sources())