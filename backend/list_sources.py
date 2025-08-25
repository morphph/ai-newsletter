#!/usr/bin/env python3
"""
List all active sources in production database
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def list_all_sources():
    """Fetch and display all sources from the database"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        sys.exit(1)
    
    client = create_client(url, key)
    
    try:
        # Fetch all sources (both active and inactive)
        response = client.table('sources').select('*').order('active', desc=True).order('source_type').order('name').execute()
        sources = response.data
        
        if not sources:
            print("No sources found in the database")
            return
        
        # Separate by type and status
        active_websites = []
        active_twitter = []
        inactive_sources = []
        
        for source in sources:
            source_data = {
                'Name': source['name'],
                'URL/Username': source.get('url') or f"@{source.get('twitter_username', 'N/A')}",
                'Type': source['source_type'],
                'Active': '✅' if source['active'] else '❌',
                'ID': source['id'][:8] + '...'  # Truncate ID for display
            }
            
            if source['active']:
                if source['source_type'] == 'twitter':
                    active_twitter.append(source_data)
                else:
                    active_websites.append(source_data)
            else:
                inactive_sources.append(source_data)
        
        # Print summary
        print("\n" + "="*80)
        print("📊 PRODUCTION SOURCES SUMMARY")
        print("="*80)
        
        total = len(sources)
        active = len(active_websites) + len(active_twitter)
        inactive = len(inactive_sources)
        
        print(f"\nTotal Sources: {total}")
        print(f"Active: {active} | Inactive: {inactive}")
        print(f"Websites: {len(active_websites)} active | Twitter: {len(active_twitter)} active")
        
        # Display active websites
        if active_websites:
            print("\n" + "="*80)
            print("🌐 ACTIVE WEBSITE SOURCES")
            print("="*80)
            for source in active_websites:
                print(f"  {source['Name']:<30} | {source['URL/Username']:<40} | {source['Active']}")
        
        # Display active Twitter sources
        if active_twitter:
            print("\n" + "="*80)
            print("🐦 ACTIVE TWITTER SOURCES")
            print("="*80)
            for source in active_twitter:
                print(f"  {source['Name']:<30} | {source['URL/Username']:<40} | {source['Active']}")
        
        # Display inactive sources
        if inactive_sources:
            print("\n" + "="*80)
            print("⏸️  INACTIVE SOURCES")
            print("="*80)
            for source in inactive_sources:
                print(f"  {source['Name']:<30} | {source['URL/Username']:<40} | {source['Active']}")
        
        # List details for active sources
        print("\n" + "="*80)
        print("📋 DETAILED SOURCE LIST")
        print("="*80)
        
        print("\n🌐 Website Sources:")
        for source in sources:
            if source['source_type'] != 'twitter' and source['active']:
                print(f"  • {source['name']}: {source['url']}")
        
        print("\n🐦 Twitter Sources:")
        for source in sources:
            if source['source_type'] == 'twitter' and source['active']:
                username = source.get('twitter_username', 'N/A')
                print(f"  • {source['name']}: @{username}")
        
    except Exception as e:
        print(f"❌ Error fetching sources: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_all_sources()