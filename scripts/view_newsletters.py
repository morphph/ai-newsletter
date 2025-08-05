import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.supabase_client import SupabaseService

async def view_newsletters():
    supabase = SupabaseService()
    
    # Get all newsletters
    newsletters = supabase.client.table('newsletters').select('*').order('sent_at', desc=True).execute()
    
    print(f"\nFound {len(newsletters.data)} newsletters in database\n")
    print("="*80)
    
    for newsletter in newsletters.data:
        print(f"ID: {newsletter['id']}")
        print(f"Sent At: {newsletter['sent_at']}")
        print(f"Subject: {newsletter['subject']}")
        print(f"\nContent Preview:")
        print("-"*80)
        print(newsletter['content'][:500] + "..." if len(newsletter['content']) > 500 else newsletter['content'])
        print("="*80)
        print()

if __name__ == "__main__":
    asyncio.run(view_newsletters())