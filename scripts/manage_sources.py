import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.supabase_client import SupabaseService

async def manage_sources():
    supabase = SupabaseService()
    
    # 1. Remove Buttondown source
    print("Removing AI News by Buttondown source...")
    try:
        result = supabase.client.table('sources').delete().eq('url', 'https://buttondown.email/ainews/archive/').execute()
        print("✓ Buttondown source removed successfully")
    except Exception as e:
        print(f"Error removing Buttondown source: {e}")
    
    # 2. Add Anthropic Research source
    print("\nAdding Anthropic Research source...")
    try:
        existing = supabase.client.table('sources').select('*').eq('url', 'https://www.anthropic.com/research').execute()
        if not existing.data:
            result = supabase.client.table('sources').insert({
                'name': 'Anthropic Research',
                'url': 'https://www.anthropic.com/research',
                'active': True
            }).execute()
            print("✓ Anthropic Research source added successfully")
        else:
            print("Anthropic Research source already exists")
    except Exception as e:
        print(f"Error adding Anthropic Research: {e}")
    
    # 3. Display all sources
    print("\nCurrent sources in database:")
    sources = supabase.client.table('sources').select('*').order('name').execute()
    
    for i, source in enumerate(sources.data, 1):
        print(f"{i}. {source['name']} - {source['url']}")
    
    print(f"\nTotal sources: {len(sources.data)}")

if __name__ == "__main__":
    asyncio.run(manage_sources())