import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.supabase_client import SupabaseService

async def update_categories():
    supabase = SupabaseService()
    
    # Define categories
    categories = {
        'Official AI Companies': [
            'OpenAI News',
            'Anthropic News',
            'Anthropic Release Notes',
            'Anthropic Research',
            'Google AI Blog',
            'Google Developers Blog',
            'Google DeepMind Blog',
            'Google Gemini Developer Blog'
        ],
        'AI Researchers & Thought Leaders': [
            'Simon Willison',
            'Hacker News',
            'Reuters AI News'
        ],
        'AI Tools': [
            'Firecrawl Blog'
        ]
    }
    
    print("Updating source categories...")
    
    for category, source_names in categories.items():
        for source_name in source_names:
            try:
                result = supabase.client.table('sources').update({
                    'category': category
                }).eq('name', source_name).execute()
                if result.data:
                    print(f"✓ Updated {source_name} -> {category}")
                else:
                    print(f"⚠ No match found for {source_name}")
            except Exception as e:
                print(f"✗ Error updating {source_name}: {e}")
    
    print("\nCurrent sources by category:")
    sources = supabase.client.table('sources').select('*').order('category', 'name').execute()
    
    current_category = None
    for source in sources.data:
        if source.get('category') != current_category:
            current_category = source.get('category', 'Uncategorized')
            print(f"\n{current_category}:")
        print(f"  - {source['name']} ({source['url']})")
    
    print(f"\nTotal sources: {len(sources.data)}")

if __name__ == "__main__":
    asyncio.run(update_categories())