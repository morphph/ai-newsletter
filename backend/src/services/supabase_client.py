import os
from typing import List, Dict, Optional
from datetime import datetime, date
from supabase import create_client, Client
from dotenv import load_dotenv

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
    
    async def check_article_exists(self, url: str) -> bool:
        response = self.client.table('articles').select('id').eq('url', url).execute()
        return len(response.data) > 0
    
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
    
