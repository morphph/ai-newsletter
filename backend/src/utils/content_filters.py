"""
Content filtering utilities for efficient pre-screening
"""

import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ContentFilter:
    """Utilities for filtering content before expensive operations"""
    
    # AI/ML related keywords for title/content filtering
    AI_KEYWORDS = [
        # Core AI terms
        'ai', 'artificial intelligence', 'machine learning', 'ml', 
        'deep learning', 'neural network', 'llm', 'large language model',
        
        # Specific models/companies
        'gpt', 'gpt-4', 'gpt-5', 'chatgpt', 'openai', 'anthropic', 'claude',
        'gemini', 'bard', 'llama', 'mistral', 'copilot', 'midjourney',
        'stable diffusion', 'dall-e', 'whisper',
        
        # AI techniques
        'transformer', 'bert', 'rag', 'retrieval augmented', 'fine-tuning',
        'prompt engineering', 'embedding', 'vector database', 'langchain',
        
        # AI applications
        'generative ai', 'computer vision', 'nlp', 'natural language',
        'chatbot', 'ai assistant', 'ai agent', 'autonomous agent',
        
        # Industry terms
        'ai startup', 'ai regulation', 'ai safety', 'ai ethics', 'agi',
        'artificial general intelligence', 'ai research', 'ai breakthrough'
    ]
    
    # Date patterns in URLs
    URL_DATE_PATTERNS = [
        r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2024/08/21/
        r'/(\d{4})-(\d{1,2})-(\d{1,2})/',  # /2024-08-21/
        r'/(\d{4})(\d{2})(\d{2})/',         # /20240821/
        r'[?&]date=(\d{4})-(\d{2})-(\d{2})', # ?date=2024-08-21
    ]
    
    # Relative date indicators in text
    RELATIVE_DATE_PATTERNS = {
        'today': 0,
        'yesterday': 1,
        '1 day ago': 1,
        'one day ago': 1,
        '2 days ago': 2,
        'two days ago': 2,
        '3 days ago': 3,
        'three days ago': 3,
    }
    
    @classmethod
    def is_ai_related_title(cls, title: str) -> bool:
        """
        Quick check if a title is likely AI-related based on keywords
        
        Args:
            title: Article title or headline
            
        Returns:
            True if title contains AI-related keywords
        """
        if not title:
            return False
            
        title_lower = title.lower()
        
        # Check for AI keywords
        for keyword in cls.AI_KEYWORDS:
            if keyword in title_lower:
                return True
        
        return False
    
    @classmethod
    def extract_date_from_url(cls, url: str) -> Optional[date]:
        """
        Try to extract publication date from URL patterns
        
        Args:
            url: Article URL
            
        Returns:
            Extracted date or None if not found
        """
        for pattern in cls.URL_DATE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) >= 3:
                        year = int(groups[0])
                        month = int(groups[1])
                        day = int(groups[2])
                        
                        # Validate date is reasonable
                        extracted_date = date(year, month, day)
                        
                        # Check if date is not too far in past or future
                        days_diff = abs((date.today() - extracted_date).days)
                        if days_diff <= 365:  # Within a year
                            return extracted_date
                            
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse date from URL pattern: {e}")
                    continue
        
        return None
    
    @classmethod
    def extract_relative_date(cls, text: str) -> Optional[date]:
        """
        Extract date from relative date text (e.g., "yesterday", "2 days ago")
        
        Args:
            text: Text containing relative date
            
        Returns:
            Calculated date or None
        """
        if not text:
            return None
            
        text_lower = text.lower()
        
        for pattern, days_ago in cls.RELATIVE_DATE_PATTERNS.items():
            if pattern in text_lower:
                return date.today() - timedelta(days=days_ago)
        
        # Check for "X hours ago" pattern (likely today or yesterday)
        hours_match = re.search(r'(\d+)\s+hours?\s+ago', text_lower)
        if hours_match:
            hours = int(hours_match.group(1))
            if hours < 24:
                return date.today()
            elif hours < 48:
                return date.today() - timedelta(days=1)
        
        return None
    
    @classmethod
    def score_article_relevance(
        cls, 
        title: str, 
        url: str, 
        snippet: str = None,
        target_date: date = None
    ) -> Tuple[float, Dict[str, any]]:
        """
        Score an article's relevance based on title, URL, and snippet
        
        Args:
            title: Article title
            url: Article URL
            snippet: Optional article snippet/description
            target_date: Target date to match (default: yesterday)
            
        Returns:
            Tuple of (score, metadata dict with findings)
        """
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        score = 0.0
        metadata = {
            'has_ai_keywords': False,
            'url_date': None,
            'relative_date': None,
            'date_matches': False,
            'ai_keywords_found': []
        }
        
        # Check AI relevance (0-50 points)
        title_lower = title.lower() if title else ""
        snippet_lower = snippet.lower() if snippet else ""
        combined_text = f"{title_lower} {snippet_lower}"
        
        ai_keywords_found = []
        for keyword in cls.AI_KEYWORDS:
            if keyword in combined_text:
                ai_keywords_found.append(keyword)
        
        if ai_keywords_found:
            metadata['has_ai_keywords'] = True
            metadata['ai_keywords_found'] = ai_keywords_found[:5]  # Top 5
            
            # More keywords = higher score
            score += min(len(ai_keywords_found) * 10, 50)
        
        # Check date relevance (0-50 points)
        url_date = cls.extract_date_from_url(url)
        if url_date:
            metadata['url_date'] = url_date.isoformat()
            if url_date == target_date:
                metadata['date_matches'] = True
                score += 50
            else:
                # Partial credit for recent dates
                days_diff = abs((target_date - url_date).days)
                if days_diff <= 3:
                    score += max(30 - days_diff * 10, 0)
        
        # Check relative dates in title/snippet
        relative_date = cls.extract_relative_date(combined_text)
        if relative_date:
            metadata['relative_date'] = relative_date.isoformat()
            if relative_date == target_date:
                metadata['date_matches'] = True
                score += 40  # Slightly less than URL date
        
        return score, metadata
    
    @classmethod
    def filter_articles_by_date(
        cls,
        articles: List[Dict],
        target_date: date = None
    ) -> List[Dict]:
        """
        Filter articles by date only (for hybrid approach)
        
        Args:
            articles: List of article dicts with 'title', 'url', and optionally 'snippet'
            target_date: Target date to match (default: yesterday)
            
        Returns:
            List of articles likely from target date
        """
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        date_matched_articles = []
        
        for article in articles:
            # Check URL for date
            url_date = cls.extract_date_from_url(article.get('url', ''))
            if url_date and url_date == target_date:
                article['date_source'] = 'url'
                article['extracted_date'] = url_date
                date_matched_articles.append(article)
                continue
            
            # Check title/snippet for relative dates
            combined_text = f"{article.get('title', '')} {article.get('snippet', '')}"
            relative_date = cls.extract_relative_date(combined_text)
            if relative_date and relative_date == target_date:
                article['date_source'] = 'text'
                article['extracted_date'] = relative_date
                date_matched_articles.append(article)
                continue
            
            # If URL has recent date (within 3 days), include with lower confidence
            if url_date and abs((target_date - url_date).days) <= 3:
                article['date_source'] = 'url_near'
                article['extracted_date'] = url_date
                article['date_confidence'] = 'low'
                date_matched_articles.append(article)
        
        logger.info(f"Date filter: {len(date_matched_articles)}/{len(articles)} articles match {target_date}")
        
        return date_matched_articles
    
    @classmethod
    def filter_articles_for_processing(
        cls,
        articles: List[Dict],
        target_date: date = None,
        min_score: float = 30.0
    ) -> List[Dict]:
        """
        Filter and rank articles for processing based on relevance
        (Legacy method - kept for compatibility)
        
        Args:
            articles: List of article dicts with 'title' and 'url'
            target_date: Target date to match
            min_score: Minimum score to include article
            
        Returns:
            Filtered and sorted list of articles
        """
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        scored_articles = []
        
        for article in articles:
            score, metadata = cls.score_article_relevance(
                title=article.get('title', ''),
                url=article.get('url', ''),
                snippet=article.get('snippet', ''),
                target_date=target_date
            )
            
            if score >= min_score:
                article['relevance_score'] = score
                article['relevance_metadata'] = metadata
                scored_articles.append(article)
        
        # Sort by score (highest first)
        scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Filtered {len(scored_articles)}/{len(articles)} articles with min_score={min_score}")
        
        return scored_articles