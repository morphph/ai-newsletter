import os
import asyncio
from typing import List, Dict, Optional
from firecrawl import AsyncFirecrawl
from dotenv import load_dotenv

load_dotenv()

class FirecrawlService:
    def __init__(self):
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY must be set in environment variables")
        self.app = AsyncFirecrawl(api_key=api_key)
    
    async def scrape_homepage(self, url: str) -> Dict:
        try:
            response = await self.app.scrape(
                url=url,
                formats=['markdown'],
                only_main_content=True,
                max_age=172800000  # 48 hours in milliseconds - avoid cached content
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
            response = await self.app.scrape(
                url=url,
                formats=['markdown'],
                only_main_content=True,
                max_age=172800000  # 48 hours in milliseconds - avoid cached content
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
    
    async def extract_article_links(self, markdown_content: str, base_url: str) -> List[Dict]:
        """Extract article links from markdown content"""
        import re
        from urllib.parse import urljoin, urlparse
        from datetime import datetime
        
        links = []
        
        # Method 1: Look for Anthropic-style news articles with dates
        # Pattern: **Title**\\n\\nDate](url)
        news_pattern = r'\*\*([^*]+)\*\*\\+\\+([^]]+)\]\(([^\)]+)\)'
        news_matches = re.findall(news_pattern, markdown_content)
        
        # Convert news matches to standard format
        matches = []
        for title, date_text, url in news_matches:
            full_title = f"{title.strip()} - {date_text.strip()}"
            matches.append((full_title, url))
        
        # Method 2: Extract regular markdown links [text](url)
        # This regex handles nested brackets better
        link_pattern = r'\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]\(([^\)]+)\)'
        regular_matches = re.findall(link_pattern, markdown_content, re.DOTALL)
        
        # Add regular matches (avoid duplicates)
        seen_urls = set(url for _, url in matches)
        for text, url in regular_matches:
            if url not in seen_urls and text and url:
                matches.append((text, url))
                seen_urls.add(url)
        
        # Skip these file extensions and patterns
        skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.css', '.js', '.pdf']
        skip_patterns = ['_next/image', '/images/', '/static/', '/assets/', '/favicon', 'utm_']
        
        for text, url in matches:
            # Skip if text is too short (likely navigation)
            if len(text.strip()) < 10:
                continue
                
            # Make URL absolute
            absolute_url = urljoin(base_url, url)
            
            # Skip non-article URLs
            url_lower = absolute_url.lower()
            if any(ext in url_lower for ext in skip_extensions):
                continue
            if any(pattern in url_lower for pattern in skip_patterns):
                continue
            
            # Filter out non-article links (social media, etc.)
            parsed = urlparse(absolute_url)
            if not parsed.netloc:
                continue
                
            # Skip social media and external non-article sites
            social_domains = ['twitter.com', 'facebook.com', 'linkedin.com', 'youtube.com', 'instagram.com']
            if any(domain in parsed.netloc for domain in social_domains):
                continue
            
            # Only include links that look like articles
            # Must be from same domain OR contain article/blog/news/post keywords
            is_same_domain = parsed.netloc == urlparse(base_url).netloc
            has_article_keywords = any(keyword in url_lower for keyword in ['/blog/', '/news/', '/article/', '/post/', '/index/', '/story/'])
            
            if is_same_domain or has_article_keywords:
                # Additional filter: URL should have some path (not just domain)
                if parsed.path and len(parsed.path) > 1:
                    # Try to extract date from title
                    date_str = None
                    # Common date patterns in article titles
                    date_patterns = [
                        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',
                        r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
                        r'\d{4}-\d{2}-\d{2}',
                        r'\d{1,2}/\d{1,2}/\d{4}'
                    ]
                    
                    for pattern in date_patterns:
                        date_match = re.search(pattern, text, re.IGNORECASE)
                        if date_match:
                            date_str = date_match.group(0)
                            break
                    
                    links.append({
                        'title': text.strip(),
                        'url': absolute_url,
                        'date_str': date_str  # Store extracted date string
                    })
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        # Sort by date if available (most recent first)
        def parse_date_for_sorting(link):
            """Helper to parse date string for sorting"""
            date_str = link.get('date_str')
            if not date_str:
                return datetime.min  # Put articles without dates at the end
            
            try:
                # Try different date formats
                for fmt in ['%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y', '%Y-%m-%d', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(date_str.replace(',', ''), fmt)
                    except:
                        continue
                return datetime.min
            except:
                return datetime.min
        
        # Sort with most recent first
        unique_links.sort(key=parse_date_for_sorting, reverse=True)
        
        # Remove the date_str field as it's no longer needed
        for link in unique_links:
            link.pop('date_str', None)
        
        return unique_links[:30]  # Return more links to ensure we get recent articles