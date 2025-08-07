import os
from typing import List, Dict, Optional
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs, urlencode
from supabase import create_client, Client
from dotenv import load_dotenv
import re

load_dotenv()

class SupabaseService:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.client: Client = create_client(url, key)
    
    async def get_active_sources(self) -> List[Dict]:
        response = self.client.table('sources').select('*').eq('active', True).execute()
        return response.data
    
    async def insert_article(self, article_data: Dict) -> Dict:
        response = self.client.table('articles').insert(article_data).execute()
        return response.data[0] if response.data else None
    
    async def get_today_articles(self, ai_related_only: bool = True) -> List[Dict]:
        query = self.client.table('articles').select('*').eq('published_at', date.today())
        if ai_related_only:
            query = query.eq('is_ai_related', True)
        response = query.execute()
        return response.data
    
    async def check_article_exists(self, url: str, headline: str = None) -> bool:
        """Enhanced deduplication with URL normalization and headline checking"""
        # Normalize URL by removing tracking parameters
        normalized_url = self._normalize_url(url)
        
        # Check by normalized URL first
        response = self.client.table('articles').select('id').or_(
            f"url.eq.{url},url.eq.{normalized_url}"
        ).execute()
        
        if len(response.data) > 0:
            return True
        
        # If headline provided, check for similar headlines from same day
        if headline:
            # Normalize the headline for comparison
            normalized_headline = self._normalize_headline(headline)
            today = date.today().isoformat()
            
            # Check for very similar headline on same day (could be same article from different source)
            response = self.client.table('articles').select('id, headline').eq(
                'published_at', today
            ).execute()
            
            for article in response.data:
                if self._are_headlines_similar(normalized_headline, article['headline']):
                    return True
        
        return False
    
    def _normalize_url(self, url: str) -> str:
        """Remove tracking parameters from URL"""
        parsed = urlparse(url)
        # Remove common tracking parameters
        params = parse_qs(parsed.query)
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 
                          'utm_term', 'ref', 'source', 'fbclid', 'gclid']
        
        cleaned_params = {k: v for k, v in params.items() if k not in tracking_params}
        
        # Rebuild URL without tracking parameters
        cleaned_query = urlencode(cleaned_params, doseq=True)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if cleaned_query:
            normalized += f"?{cleaned_query}"
        
        return normalized
    
    def _normalize_headline(self, headline: str) -> str:
        """Normalize headline for comparison"""
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', '', headline.lower())
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _are_headlines_similar(self, headline1: str, headline2: str) -> bool:
        """Check if two headlines are similar enough to be the same article"""
        h1 = self._normalize_headline(headline1)
        h2 = self._normalize_headline(headline2)
        
        # Exact match after normalization
        if h1 == h2:
            return True
        
        # Check if one is substring of the other (common with different sources)
        if len(h1) > 10 and len(h2) > 10:
            if h1 in h2 or h2 in h1:
                return True
        
        # Check word overlap (at least 80% common words for headlines > 5 words)
        words1 = set(h1.split())
        words2 = set(h2.split())
        
        if len(words1) > 5 and len(words2) > 5:
            common = words1.intersection(words2)
            total = min(len(words1), len(words2))
            if len(common) / total >= 0.8:
                return True
        
        return False
    
    async def update_article_summary(self, article_id: str, summary: str, is_ai_related: bool) -> Dict:
        response = self.client.table('articles').update({
            'summary': summary,
            'is_ai_related': is_ai_related
        }).eq('id', article_id).execute()
        return response.data[0] if response.data else None
    
    async def update_article_full_content(self, article_id: str, full_content: str) -> Dict:
        response = self.client.table('articles').update({
            'full_content': full_content
        }).eq('id', article_id).execute()
        return response.data[0] if response.data else None
    
    async def log_source_stats(self, source_id: str, stats: Dict) -> None:
        """Log source crawl statistics for monitoring"""
        try:
            # Check if stats for today already exist
            today = date.today().isoformat()
            existing = self.client.table('source_stats').select('id').eq(
                'source_id', source_id
            ).eq('crawl_date', today).execute()
            
            stats_data = {
                'source_id': source_id,
                'crawl_date': today,
                'success_count': stats.get('success_count', 0),
                'failure_count': stats.get('failure_count', 0),
                'articles_found': stats.get('articles_found', 0),
                'new_articles': stats.get('new_articles', 0),
                'last_error': stats.get('last_error', None)
            }
            
            if existing.data:
                # Update existing stats
                self.client.table('source_stats').update(stats_data).eq(
                    'id', existing.data[0]['id']
                ).execute()
            else:
                # Insert new stats
                self.client.table('source_stats').insert(stats_data).execute()
        except Exception as e:
            print(f"Error logging source stats: {e}")
    
    async def get_source_health(self, days: int = 7) -> Dict:
        """Get source health statistics for monitoring"""
        from datetime import timedelta
        
        since_date = (date.today() - timedelta(days=days)).isoformat()
        
        response = self.client.table('source_stats').select(
            '*, sources!inner(name)'
        ).gte('crawl_date', since_date).execute()
        
        health_report = {}
        for stat in response.data:
            source_name = stat['sources']['name']
            if source_name not in health_report:
                health_report[source_name] = {
                    'total_crawls': 0,
                    'successful_crawls': 0,
                    'failed_crawls': 0,
                    'total_articles': 0,
                    'last_error': None
                }
            
            health_report[source_name]['total_crawls'] += 1
            if stat['success_count'] > 0:
                health_report[source_name]['successful_crawls'] += 1
            if stat['failure_count'] > 0:
                health_report[source_name]['failed_crawls'] += 1
            health_report[source_name]['total_articles'] += stat.get('new_articles', 0)
            if stat.get('last_error'):
                health_report[source_name]['last_error'] = stat['last_error']
        
        return health_report
    
