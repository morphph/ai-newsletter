import os
import asyncio
from typing import List, Dict, Optional
from firecrawl import AsyncFirecrawlApp
from dotenv import load_dotenv

load_dotenv()

class FirecrawlService:
    def __init__(self):
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY must be set in environment variables")
        self.app = AsyncFirecrawlApp(api_key=api_key)
    
    async def scrape_homepage(self, url: str) -> Dict:
        try:
            response = await self.app.scrape_url(
                url=url,
                formats=['markdown'],
                only_main_content=True
            )
            
            # Handle the response object directly
            if response and hasattr(response, 'markdown'):
                return {
                    'success': True,
                    'markdown': response.markdown or '',
                    'metadata': response.metadata if hasattr(response, 'metadata') else {}
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to scrape URL',
                    'details': str(response)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def scrape_article(self, url: str) -> Dict:
        try:
            response = await self.app.scrape_url(
                url=url,
                formats=['markdown'],
                only_main_content=True
            )
            
            # Handle the response object directly
            if response and hasattr(response, 'markdown'):
                metadata = response.metadata if hasattr(response, 'metadata') else {}
                return {
                    'success': True,
                    'markdown': response.markdown or '',
                    'title': metadata.get('title', '') if isinstance(metadata, dict) else '',
                    'description': metadata.get('description', '') if isinstance(metadata, dict) else '',
                    'published_date': metadata.get('publishedDate', '') if isinstance(metadata, dict) else ''
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to scrape article',
                    'details': str(response)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        tasks = [self.scrape_article(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results