#!/usr/bin/env python3
"""
Script to manage Twitter/X sources in the database
Allows adding, listing, and managing Twitter accounts as news sources
"""

import os
import sys
import argparse
from datetime import datetime
from uuid import uuid4
from typing import List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.src.services.supabase_client import SupabaseService
from backend.src.services.twitter_service import TwitterService
from backend.src.utils.twitter_utils import parse_twitter_input, validate_twitter_username
from dotenv import load_dotenv

load_dotenv()


class TwitterSourceManager:
    """Manager for Twitter sources"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.twitter = TwitterService()
    
    def add_twitter_source(
        self, 
        input_str: str, 
        name: Optional[str] = None,
        category: str = "AI Influencers"
    ) -> bool:
        """
        Add a new Twitter source to the database
        
        Args:
            input_str: Twitter URL, handle, or "handle:Display Name" format
            name: Display name for the source (overrides extracted name)
            category: Category for the source
            
        Returns:
            True if successful, False otherwise
        """
        # Parse input to extract username and optional display name
        username, extracted_name = parse_twitter_input(input_str)
        
        if not username:
            print(f"✗ Invalid Twitter input: {input_str}")
            print("  Accepted formats: @username, username, https://twitter.com/username, username:Display Name")
            return False
        
        # Validate username
        if not validate_twitter_username(username):
            print(f"✗ Invalid Twitter username: {username}")
            print("  Username must be 1-15 characters, only letters, numbers, and underscores")
            return False
        
        # Use provided name, or extracted name, or default to @username
        if not name:
            name = extracted_name if extracted_name else f"@{username}"
        
        # Check if already exists
        existing = self.supabase.client.table('sources').select('*').eq(
            'twitter_username', username
        ).execute()
        
        if existing.data:
            print(f"✗ Twitter source @{username} already exists")
            return False
        
        # Create source record
        source_data = {
            'id': str(uuid4()),
            'name': name,
            'url': f"https://twitter.com/{username}",
            'source_type': 'twitter',
            'twitter_username': username,
            'category': category,
            'active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            result = self.supabase.client.table('sources').insert(source_data).execute()
            if result.data:
                print(f"✓ Added Twitter source: @{username} ({name})")
                return True
            else:
                print(f"✗ Failed to add Twitter source @{username}")
                return False
        except Exception as e:
            print(f"✗ Error adding Twitter source: {str(e)}")
            return False
    
    def list_twitter_sources(self, active_only: bool = True) -> List[dict]:
        """
        List all Twitter sources
        
        Args:
            active_only: Only show active sources
            
        Returns:
            List of Twitter sources
        """
        query = self.supabase.client.table('sources').select('*').eq(
            'source_type', 'twitter'
        )
        
        if active_only:
            query = query.eq('active', True)
        
        result = query.order('name').execute()
        
        return result.data if result.data else []
    
    def toggle_source(self, input_str: str, active: bool) -> bool:
        """
        Activate or deactivate a Twitter source
        
        Args:
            input_str: Twitter URL or username
            active: New active status
            
        Returns:
            True if successful
        """
        username, _ = parse_twitter_input(input_str)
        
        if not username:
            print(f"✗ Invalid Twitter input: {input_str}")
            return False
        
        try:
            result = self.supabase.client.table('sources').update({
                'active': active
            }).eq('twitter_username', username).execute()
            
            if result.data:
                status = "activated" if active else "deactivated"
                print(f"✓ Twitter source @{username} {status}")
                return True
            else:
                print(f"✗ Twitter source @{username} not found")
                return False
        except Exception as e:
            print(f"✗ Error updating source: {str(e)}")
            return False
    
    def test_twitter_source(self, input_str: str, limit: int = 5) -> bool:
        """
        Test fetching tweets from a Twitter source
        
        Args:
            input_str: Twitter URL or username to test
            limit: Number of tweets to fetch
            
        Returns:
            True if successful
        """
        import asyncio
        
        username, _ = parse_twitter_input(input_str)
        
        if not username:
            print(f"✗ Invalid Twitter input: {input_str}")
            return False
        
        print(f"Testing Twitter source @{username}...")
        
        async def test():
            try:
                tweets = await self.twitter.fetch_user_tweets(username, limit=limit)
                
                if tweets:
                    print(f"✓ Successfully fetched {len(tweets)} tweets from @{username}:")
                    for i, tweet in enumerate(tweets[:3], 1):
                        headline = tweet['headline'][:80] + "..." if len(tweet['headline']) > 80 else tweet['headline']
                        print(f"  {i}. {headline}")
                        print(f"     Date: {tweet['published_at']}, Likes: {tweet['like_count']}")
                    
                    if len(tweets) > 3:
                        print(f"  ... and {len(tweets) - 3} more tweets")
                    
                    return True
                else:
                    print(f"✗ No tweets found for @{username}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error fetching tweets: {str(e)}")
                return False
        
        return asyncio.run(test())
    
    def get_source_stats(self) -> dict:
        """Get statistics about sources"""
        # Get all sources
        all_sources = self.supabase.client.table('sources').select('*').execute()
        
        # Get Twitter sources
        twitter_sources = [s for s in all_sources.data if s.get('source_type') == 'twitter']
        website_sources = [s for s in all_sources.data if s.get('source_type') in ['website', None]]
        
        # Get article counts
        stats = {
            'total_sources': len(all_sources.data),
            'twitter_sources': len(twitter_sources),
            'website_sources': len(website_sources),
            'active_twitter': len([s for s in twitter_sources if s.get('active')]),
            'active_websites': len([s for s in website_sources if s.get('active')])
        }
        
        return stats


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Manage Twitter/X sources for AI news aggregation"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a Twitter source')
    add_parser.add_argument('input', help='Twitter URL, @handle, or "handle:Display Name"')
    add_parser.add_argument('--name', help='Display name (overrides extracted name)')
    add_parser.add_argument('--category', default='AI Influencers', help='Category for the source')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List Twitter sources')
    list_parser.add_argument('--all', action='store_true', help='Include inactive sources')
    
    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Activate a Twitter source')
    activate_parser.add_argument('input', help='Twitter URL or @handle')
    
    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a Twitter source')
    deactivate_parser.add_argument('input', help='Twitter URL or @handle')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test fetching from a Twitter source')
    test_parser.add_argument('input', help='Twitter URL or @handle to test')
    test_parser.add_argument('--limit', type=int, default=5, help='Number of tweets to fetch')
    
    # Add batch command
    batch_parser = subparsers.add_parser('add-batch', help='Add multiple Twitter sources from a file')
    batch_parser.add_argument('file', help='File containing Twitter URLs/handles (one per line)')
    batch_parser.add_argument('--category', default='AI Influencers', help='Category for all sources')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show source statistics')
    
    # Add default sources command
    default_parser = subparsers.add_parser('add-defaults', help='Add default AI Twitter sources')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TwitterSourceManager()
    
    if args.command == 'add':
        manager.add_twitter_source(args.input, args.name, args.category)
    
    elif args.command == 'add-batch':
        try:
            with open(args.file, 'r') as f:
                lines = f.readlines()
            
            print(f"Adding {len(lines)} Twitter sources from {args.file}...")
            success_count = 0
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    if manager.add_twitter_source(line, category=args.category):
                        success_count += 1
            
            print(f"\nAdded {success_count}/{len([l for l in lines if l.strip() and not l.startswith('#')])} sources")
        except FileNotFoundError:
            print(f"✗ File not found: {args.file}")
        except Exception as e:
            print(f"✗ Error reading file: {str(e)}")
    
    elif args.command == 'list':
        sources = manager.list_twitter_sources(active_only=not args.all)
        
        if sources:
            print(f"\n{'Active' if not args.all else 'All'} Twitter Sources:")
            print("-" * 60)
            for source in sources:
                status = "✓" if source['active'] else "✗"
                print(f"{status} @{source['twitter_username']} - {source['name']}")
                print(f"  Category: {source.get('category', 'N/A')}")
                print(f"  Created: {source['created_at'][:10]}")
                print()
        else:
            print("No Twitter sources found")
    
    elif args.command == 'activate':
        manager.toggle_source(args.input, True)
    
    elif args.command == 'deactivate':
        manager.toggle_source(args.input, False)
    
    elif args.command == 'test':
        manager.test_twitter_source(args.input, args.limit)
    
    elif args.command == 'stats':
        stats = manager.get_source_stats()
        print("\nSource Statistics:")
        print("-" * 40)
        print(f"Total sources: {stats['total_sources']}")
        print(f"  Twitter sources: {stats['twitter_sources']} ({stats['active_twitter']} active)")
        print(f"  Website sources: {stats['website_sources']} ({stats['active_websites']} active)")
    
    elif args.command == 'add-defaults':
        # Add default AI influencer Twitter accounts (40+ curated sources)
        default_accounts = [
            # AI Researchers
            ('karpathy', 'Andrej Karpathy', 'AI Researchers'),
            ('ylecun', 'Yann LeCun', 'AI Researchers'),
            ('geoffreyhinton', 'Geoffrey Hinton', 'AI Researchers'),
            ('drjimfan', 'Jim Fan - NVIDIA', 'AI Researchers'),
            ('goodfellow_ian', 'Ian Goodfellow', 'AI Researchers'),
            ('fchollet', 'François Chollet', 'AI Researchers'),
            ('hardmaru', 'David Ha', 'AI Researchers'),
            ('OriolVinyalsML', 'Oriol Vinyals', 'AI Researchers'),
            
            # AI Leaders & Executives
            ('sama', 'Sam Altman - OpenAI', 'AI Leaders'),
            ('demishassabis', 'Demis Hassabis - DeepMind', 'AI Leaders'),
            ('AndrewYNg', 'Andrew Ng', 'AI Leaders'),
            ('gdb', 'Greg Brockman - OpenAI', 'AI Leaders'),
            ('ilyasut', 'Ilya Sutskever', 'AI Leaders'),
            ('clementdelangue', 'Clement Delangue - HuggingFace', 'AI Leaders'),
            
            # AI Critics & Ethics
            ('GaryMarcus', 'Gary Marcus', 'AI Critics'),
            ('emilymbender', 'Emily M. Bender', 'AI Critics'),
            ('timnitGebru', 'Timnit Gebru', 'AI Critics'),
            ('mmitchell_ai', 'Margaret Mitchell', 'AI Critics'),
            
            # AI Educators & Influencers
            ('emollick', 'Ethan Mollick', 'AI Educators'),
            ('lexfridman', 'Lex Fridman', 'AI Educators'),
            ('rasbt', 'Sebastian Raschka', 'AI Educators'),
            ('_akhaliq', 'AK', 'AI Educators'),
            ('karinanguyen_', 'Karina Nguyen', 'AI Educators'),
            
            # AI Engineers & Builders
            ('simonw', 'Simon Willison', 'AI Engineers'),
            ('jxnlco', 'Jason Liu', 'AI Engineers'),
            ('aparnadhinak', 'Aparna Dhinakaran', 'AI Engineers'),
            ('vboykis', 'Vicki Boykis', 'AI Engineers'),
            ('swyx', 'Shawn Wang', 'AI Engineers'),
            ('transitive_bs', 'Logan Kilpatrick', 'AI Engineers'),
            ('alvinfoo', 'Alvin Foo', 'AI Engineers'),
            
            # AI Companies & Organizations
            ('OpenAI', 'OpenAI', 'AI Companies'),
            ('DeepMind', 'DeepMind', 'AI Companies'),
            ('AnthropicAI', 'Anthropic', 'AI Companies'),
            ('MistralAI', 'Mistral AI', 'AI Companies'),
            ('StabilityAI', 'Stability AI', 'AI Companies'),
            ('weights_biases', 'Weights & Biases', 'AI Companies'),
            ('huggingface', 'Hugging Face', 'AI Companies'),
            ('CohereAI', 'Cohere', 'AI Companies'),
            
            # AI News & Media
            ('TheAIEdge', 'The AI Edge', 'AI News'),
            ('MIT_CSAIL', 'MIT CSAIL', 'AI News'),
            ('DeepLearningAI', 'DeepLearning.AI', 'AI News'),
        ]
        
        print("Adding default AI Twitter sources...")
        success_count = 0
        
        for username, name, category in default_accounts:
            if manager.add_twitter_source(username, name, category):
                success_count += 1
        
        print(f"\nAdded {success_count}/{len(default_accounts)} default sources")


if __name__ == "__main__":
    main()