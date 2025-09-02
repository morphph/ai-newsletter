import os
import json
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def filter_ai_articles(self, markdown_content: str, source_url: str) -> List[Dict]:
        today = date.today()
        yesterday = (today - timedelta(days=1))
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        system_prompt = f"""You are an AI news curator. Extract articles that meet these criteria:
1. MUST be related to AI, machine learning, LLMs, or artificial intelligence
2. MUST be from yesterday ({yesterday_str}) - look for this specific date or "yesterday" indicators
3. MUST have both a headline and a link
4. Extract the actual publication date when available

Focus on finding articles from {yesterday_str} by looking for:
- Explicit date: "{yesterday_str}", "{yesterday.strftime('%B %d, %Y')}", "{yesterday.strftime('%b %d, %Y')}"
- Relative indicators: "yesterday", "1 day ago" (if today is {today.strftime('%Y-%m-%d')})
- Date metadata or timestamps matching yesterday

Return a JSON object with an 'articles' array containing objects with:
- headline: the article title
- link: absolute URL
- date: actual publication date in YYYY-MM-DD format (should be {yesterday_str} for most)
- confidence: 'high' if date is explicit, 'medium' if inferred, 'low' if unsure

Example: {{"articles": [{{"headline": "...", "link": "...", "date": "{yesterday_str}", "confidence": "high"}}]}}"""

        user_prompt = f"""Extract AI-related articles from this content:
Source URL: {source_url}
Content:
{markdown_content}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            articles = result.get('articles', [])
            if not isinstance(articles, list):
                articles = []
            
            for article in articles:
                if not article.get('link', '').startswith('http'):
                    if source_url.endswith('/'):
                        article['link'] = source_url + article['link'].lstrip('/')
                    else:
                        article['link'] = source_url + '/' + article['link'].lstrip('/')
            
            return articles
            
        except Exception as e:
            print(f"Error filtering articles: {e}")
            return []
    
    async def summarize_article(self, article_content: str, headline: str) -> Dict[str, str]:
        system_prompt = """You are a professional newsletter writer. Create a 2-3 sentence summary of the given article that:
1. Captures the key innovation or announcement
2. Explains why it matters to AI practitioners
3. Is engaging and informative

Also determine if this article is truly AI/ML related (return true/false).

Return your response as JSON with two fields: "summary" and "is_ai_related"."""

        user_prompt = f"""Article Headline: {headline}

Article Content:
{article_content[:8000]}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return {
                'summary': result.get('summary', ''),
                'is_ai_related': result.get('is_ai_related', True)
            }
            
        except Exception as e:
            print(f"Error summarizing article: {e}")
            return {
                'summary': '',
                'is_ai_related': False
            }
    
    async def generate_newsletter(self, articles: List[Dict]) -> Dict[str, str]:
        today = date.today().strftime('%B %d, %Y')
        
        articles_text = "\n\n".join([
            f"**{i+1}. {article['headline']}**\n"
            f"Source: {article['source_name']}\n"
            f"Link: {article['url']}\n"
            f"Summary: {article['summary']}"
            for i, article in enumerate(articles[:10])
        ])
        
        system_prompt = """You are a professional AI newsletter writer. Create an engaging newsletter that:
1. Has a catchy subject line
2. Includes a brief introduction
3. Presents the articles in an organized, readable format
4. Ends with a brief conclusion

Make it informative yet conversational. The tone should be professional but approachable."""

        user_prompt = f"""Create a newsletter for {today} with these top AI stories:

{articles_text}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_completion_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            lines = content.split('\n')
            subject = lines[0].replace('Subject:', '').strip() if lines else f"AI Newsletter - {today}"
            body = '\n'.join(lines[1:]) if len(lines) > 1 else content
            
            return {
                'subject': subject,
                'content': body
            }
            
        except Exception as e:
            print(f"Error generating newsletter: {e}")
            return {
                'subject': f"AI Newsletter - {today}",
                'content': articles_text
            }
    
    async def generate_summary(self, prompt: str, max_tokens: int = 100) -> str:
        """Generate a summary based on the provided prompt"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return ""
    
    async def evaluate_articles_batch(self, articles: List[Dict], target_date: date = None) -> List[Dict]:
        """
        Evaluate multiple articles for AI relevance in a single GPT call
        
        Args:
            articles: List of dicts with 'title', 'url', and optionally 'snippet'
            target_date: Date to verify articles are from (optional)
            
        Returns:
            List of articles that are AI-related
        """
        if not articles:
            return []
        
        # Prepare articles for GPT evaluation
        articles_text = "\n\n".join([
            f"Title: {art.get('title', 'No title')}\n"
            f"URL: {art.get('url', '')}\n"
            f"Snippet: {art.get('snippet', '')[:200] if art.get('snippet') else 'No snippet'}"
            for i, art in enumerate(articles[:30], 1)  # Limit to 30 articles
        ])
        
        date_context = f" from {target_date.isoformat()}" if target_date else ""
        
        system_prompt = f"""You are an AI content curator. Analyze the following articles{date_context} and identify which ones are about:
- Artificial Intelligence, Machine Learning, Deep Learning
- Large Language Models (GPT, Claude, Gemini, LLaMA, etc.)
- AI research, papers, breakthroughs, or technical developments
- AI tools, frameworks, or applications
- AI companies, funding, acquisitions, or business news
- AI ethics, safety, regulation, or policy
- Computer vision, NLP, robotics with AI focus
- Generative AI, AGI, or AI agents

Return a JSON object with an 'ai_articles' array containing the URLs of articles that are AI-related.
Be selective - only include articles with clear AI/ML focus, not just tech news that mentions AI in passing.

Format: {{"ai_articles": ["url1", "url2", ...]}}"""

        user_prompt = f"""Identify which of these articles are about AI/ML topics:

{articles_text}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use faster model for screening
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            ai_urls = set(result.get('ai_articles', []))
            
            # Return only articles that GPT identified as AI-related
            ai_articles = [
                article for article in articles 
                if article.get('url') in ai_urls
            ]
            
            return ai_articles
            
        except Exception as e:
            print(f"Error evaluating articles batch: {e}")
            # Fallback: return articles with obvious AI keywords
            ai_keywords = ['ai', 'gpt', 'llm', 'machine learning', 'neural', 'openai', 'anthropic']
            return [
                art for art in articles
                if any(keyword in (art.get('title', '') + art.get('snippet', '')).lower() 
                       for keyword in ai_keywords)
            ]
    
    async def evaluate_articles_date_and_ai(self, articles: List[Dict], target_date: date) -> List[Dict]:
        """
        Evaluate articles for BOTH date relevance AND AI relevance in a single GPT call.
        This replaces the two-step Python date filter + AI filter with a single GPT evaluation.
        
        Args:
            articles: List of dicts with 'title', 'url', and optionally 'snippet'
            target_date: The specific date to filter for (usually yesterday)
            
        Returns:
            List of articles that are BOTH from target_date AND AI-related
        """
        if not articles:
            return []
        
        # Prepare all articles for GPT evaluation (no pre-filtering!)
        articles_text = "\n\n".join([
            f"Article {i}:\n"
            f"Title: {art.get('title', 'No title')}\n"
            f"URL: {art.get('url', '')}\n"
            f"Snippet: {art.get('snippet', '')[:300] if art.get('snippet') else 'No snippet'}"
            for i, art in enumerate(articles[:50], 1)  # Increased limit to evaluate more articles
        ])
        
        # Format dates for GPT to understand
        target_date_str = target_date.strftime('%Y-%m-%d')
        target_date_readable = target_date.strftime('%B %d, %Y')
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        
        # Calculate relative date context
        days_ago = (today - target_date).days
        relative_context = ""
        if days_ago == 1:
            relative_context = "yesterday"
        elif days_ago == 0:
            relative_context = "today"
        else:
            relative_context = f"{days_ago} days ago"
        
        system_prompt = f"""You are an AI news curator with expertise in identifying article dates and AI relevance.
        
Your task is to identify articles that meet BOTH criteria:
1. Published on {target_date_str} ({target_date_readable}, which is {relative_context} relative to {today_str})
2. Related to AI/ML topics

For date identification, look for:
- Explicit dates in URLs (e.g., /2024/08/30/, /2024-08-30/)
- Date mentions in titles or snippets
- Relative date indicators (e.g., "yesterday", "today", "1 day ago" relative to {today_str})
- Publication dates in metadata or text
- Be flexible: articles published on {target_date_str} might show various date formats

For AI relevance, look for content about:
- Artificial Intelligence, Machine Learning, Deep Learning, Neural Networks
- Large Language Models (GPT, Claude, Gemini, LLaMA, Mistral, etc.)
- AI research, papers, benchmarks, breakthroughs
- AI tools, APIs, frameworks (LangChain, HuggingFace, etc.)
- AI companies, funding, acquisitions, product launches
- AI ethics, safety, alignment, regulation, policy
- Computer vision, NLP, robotics with AI focus
- Generative AI, AGI, AI agents, automation

Return a JSON object with an 'articles' array containing objects for articles that meet BOTH criteria:
{{"articles": [{{"index": 1, "url": "...", "confidence": "high|medium|low", "date_found": "url|title|snippet|inferred", "reason": "brief explanation"}}]}}

Be thorough but selective - only include articles clearly from {target_date_str} AND clearly about AI/ML."""

        user_prompt = f"""Analyze these articles and identify which ones are BOTH from {target_date_str} AND about AI/ML:

{articles_text}

Remember: Today is {today_str}, so {target_date_str} is {relative_context}."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using faster model for efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Extract the filtered articles
            filtered_results = result.get('articles', [])
            
            # Map back to original articles
            ai_and_date_articles = []
            for item in filtered_results:
                index = item.get('index', 0) - 1  # Convert to 0-based index
                if 0 <= index < len(articles):
                    article = articles[index].copy()
                    # Add metadata from GPT's analysis
                    article['gpt_confidence'] = item.get('confidence', 'unknown')
                    article['date_source'] = item.get('date_found', 'unknown')
                    article['gpt_reason'] = item.get('reason', '')
                    ai_and_date_articles.append(article)
            
            print(f"GPT evaluated {len(articles)} articles, found {len(ai_and_date_articles)} matching both date ({target_date_str}) and AI criteria")
            
            return ai_and_date_articles
            
        except Exception as e:
            print(f"Error in evaluate_articles_date_and_ai: {e}")
            # Fallback to simple keyword matching if GPT fails
            ai_keywords = ['ai', 'artificial intelligence', 'gpt', 'llm', 'machine learning', 
                          'deep learning', 'neural', 'openai', 'anthropic', 'claude', 'gemini']
            
            fallback_articles = []
            for art in articles:
                # Check for AI keywords
                text = (art.get('title', '') + ' ' + art.get('snippet', '')).lower()
                has_ai = any(keyword in text for keyword in ai_keywords)
                
                # Check for date in URL
                url = art.get('url', '')
                date_patterns = [
                    target_date.strftime('/%Y/%m/%d/'),
                    target_date.strftime('/%Y-%m-%d/'),
                    target_date.strftime('/%Y%m%d/')
                ]
                has_date = any(pattern in url for pattern in date_patterns)
                
                if has_ai and has_date:
                    fallback_articles.append(art)
            
            print(f"Fallback: Found {len(fallback_articles)} articles with AI keywords and date in URL")
            return fallback_articles
    
    async def extract_and_filter_articles(self, markdown_content: str, base_url: str, target_date: date) -> List[Dict]:
        """
        Extract article links from homepage markdown and filter for BOTH date AND AI relevance.
        This combines link extraction and filtering in a single GPT call for efficiency.
        
        Args:
            markdown_content: The full homepage markdown from Firecrawl
            base_url: The base URL of the website for converting relative URLs
            target_date: The specific date to filter for (usually yesterday)
            
        Returns:
            List of articles with rich metadata that match both date and AI criteria
        """
        if not markdown_content:
            return []
        
        # Format dates for GPT
        target_date_str = target_date.strftime('%Y-%m-%d')
        target_date_readable = target_date.strftime('%B %d, %Y')
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        
        # Calculate relative date context
        days_ago = (today - target_date).days
        relative_context = ""
        if days_ago == 1:
            relative_context = "yesterday"
        elif days_ago == 0:
            relative_context = "today"
        else:
            relative_context = f"{days_ago} days ago"
        
        system_prompt = f"""You are an AI news curator that extracts and filters articles from website homepages.
        
Your task:
1. Extract ALL article links from the markdown content
2. Filter for articles that meet BOTH criteria:
   - Published on {target_date_str} ({target_date_readable}, which is {relative_context} relative to {today_str})
   - Related to AI/ML/LLM topics

For date identification, look for:
- Explicit dates in URLs (e.g., /2025/09/01/, /2025-09-01/)
- Date mentions in link text or nearby content
- Relative date indicators ("yesterday", "today", "1 day ago" relative to {today_str})
- Publication dates in the markdown content
- Be flexible with date formats but strict about the actual date

For AI relevance, look for content about:
- Artificial Intelligence, Machine Learning, Deep Learning, Neural Networks
- Large Language Models (GPT, Claude, Gemini, LLaMA, Mistral, Llama, etc.)
- AI companies (OpenAI, Anthropic, Google AI, Meta AI, Microsoft AI, etc.)
- AI research, papers, benchmarks, breakthroughs
- AI tools, APIs, frameworks (LangChain, HuggingFace, TensorFlow, PyTorch, etc.)
- AI applications, products, services
- Generative AI, AGI, AI agents, AI assistants
- Computer vision, NLP, robotics with AI focus
- AI ethics, safety, alignment, regulation, policy

Convert any relative URLs to absolute URLs using base URL: {base_url}

Return a JSON object with an 'articles' array containing detailed metadata:
{{
  "articles": [
    {{
      "url": "https://example.com/2025/09/01/ai-article",
      "title": "Article Title",
      "published_date": "{target_date_str}",
      "date_confidence": "high|medium|low",
      "date_source": "url|text|metadata|inferred",
      "ai_relevance_score": 0.95,
      "ai_keywords": ["OpenAI", "GPT", "LLM"],
      "snippet": "Brief excerpt from the article...",
      "reason": "URL contains date, title mentions OpenAI and GPT"
    }}
  ]
}}

Be selective - only include articles clearly from {target_date_str} AND clearly about AI/ML.
If no articles match both criteria, return an empty articles array."""

        user_prompt = f"""Extract and filter AI articles from {target_date_str} in this homepage content:

{markdown_content[:15000]}  # Limit content size for token efficiency

Base URL: {base_url}
Today's date: {today_str}
Target date: {target_date_str} ({relative_context})"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            articles = result.get('articles', [])
            
            # Ensure all URLs are absolute
            from urllib.parse import urljoin
            for article in articles:
                if not article.get('url', '').startswith('http'):
                    article['url'] = urljoin(base_url, article['url'])
            
            print(f"GPT extracted and filtered {len(articles)} articles from {target_date_str} that are AI-related")
            
            # Log some details for debugging
            if articles:
                high_conf = sum(1 for a in articles if a.get('date_confidence') == 'high')
                med_conf = sum(1 for a in articles if a.get('date_confidence') == 'medium')
                low_conf = sum(1 for a in articles if a.get('date_confidence') == 'low')
                print(f"  Date confidence: {high_conf} high, {med_conf} medium, {low_conf} low")
                
                avg_ai_score = sum(a.get('ai_relevance_score', 0) for a in articles) / len(articles)
                print(f"  Average AI relevance score: {avg_ai_score:.2f}")
            
            return articles
            
        except Exception as e:
            print(f"Error in extract_and_filter_articles: {e}")
            return []
    
    async def evaluate_tweets_batch(self, tweets: List[Dict], target_date: date = None) -> List[Dict]:
        """
        Evaluate multiple tweets for AI relevance in a single GPT call
        
        Args:
            tweets: List of tweet dicts with 'content', 'author_username', etc.
            target_date: Date tweets are from (for context)
            
        Returns:
            List of tweets that are AI-related
        """
        if not tweets:
            return []
        
        # Prepare tweets for GPT evaluation
        tweets_text = "\n\n".join([
            f"@{tweet.get('author_username', 'unknown')}: {tweet.get('content', '')[:280]}"
            for tweet in tweets[:50]  # Limit to 50 tweets
        ])
        
        date_context = f" from {target_date.isoformat()}" if target_date else ""
        
        system_prompt = f"""You are an AI content curator analyzing tweets{date_context}. Identify which tweets are about:
- Artificial Intelligence, Machine Learning, Deep Learning, Neural Networks
- Large Language Models (GPT, Claude, Gemini, LLaMA, Mistral, etc.)
- AI research, papers, benchmarks, or technical developments
- AI tools, APIs, frameworks (LangChain, HuggingFace, etc.)
- AI companies, funding, product launches, or updates
- AI ethics, safety, alignment, regulation, or policy
- Computer vision, NLP, robotics with AI focus
- Generative AI, AGI, AI agents, or automation

Return a JSON object with a 'tweet_indices' array containing the 0-based indices of AI-related tweets.
Be selective - only include tweets with clear AI/ML focus, not general tech tweets.

Format: {{"tweet_indices": [0, 2, 5, ...]}}"""

        user_prompt = f"""Identify which of these tweets are about AI/ML topics:

{tweets_text}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast model for screening
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            ai_indices = set(result.get('tweet_indices', []))
            
            # Return only tweets that GPT identified as AI-related
            ai_tweets = [
                tweet for i, tweet in enumerate(tweets[:50])
                if i in ai_indices
            ]
            
            return ai_tweets
            
        except Exception as e:
            print(f"Error evaluating tweets batch: {e}")
            # Fallback: return tweets with obvious AI keywords
            ai_keywords = ['ai', 'gpt', 'llm', 'claude', 'gemini', 'machine learning', 'neural']
            return [
                tweet for tweet in tweets
                if any(keyword in tweet.get('content', '').lower() 
                       for keyword in ai_keywords)
            ]
    
    async def check_tweet_ai_relevance(self, tweet_content: str, headline: str) -> bool:
        """Check if a tweet is AI/ML related"""
        system_prompt = """You are an AI content curator. Determine if the given tweet is related to:
- Artificial Intelligence, Machine Learning, Deep Learning
- Large Language Models (LLMs), GPT, Claude, Gemini, etc.
- AI research, papers, breakthroughs
- AI tools, applications, or frameworks
- AI ethics, policy, or industry news
- Computer vision, NLP, robotics with AI
- AI startups, funding, or business developments

Return JSON with a single field "is_ai_related" (true/false)."""

        user_prompt = f"""Tweet: {tweet_content}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return result.get('is_ai_related', False)
            
        except Exception as e:
            print(f"Error checking tweet AI relevance: {e}")
            # Default to False if error
            return False
    
    async def summarize_tweet(self, tweet_content: str, author: str, headline: str) -> Dict[str, str]:
        """Summarize a tweet for the newsletter"""
        system_prompt = """You are a professional newsletter writer. Create a 1-2 sentence summary of the given tweet that:
1. Captures the key insight or announcement
2. Maintains the author's voice and perspective
3. Explains why it matters to AI practitioners

Also determine if this tweet is truly AI/ML related (return true/false).

Return your response as JSON with two fields: "summary" and "is_ai_related"."""

        user_prompt = f"""Tweet from @{author}:
{tweet_content}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return {
                'summary': result.get('summary', ''),
                'is_ai_related': result.get('is_ai_related', True)
            }
            
        except Exception as e:
            print(f"Error summarizing tweet: {e}")
            return {
                'summary': '',
                'is_ai_related': False
            }
    
    async def check_content_ai_relevance(self, content: str, headline: str) -> bool:
        """Check if content is AI-related (generic method for both tweets and articles)"""
        return await self.check_tweet_ai_relevance(content, headline)
    
    async def generate_tweet_summary(self, content: str, author: str) -> str:
        """Generate summary for tweet content"""
        result = await self.summarize_tweet(content, author, content[:50])
        return result.get("summary", content[:100])
    
    async def extract_tags(self, content: str) -> List[str]:
        """Extract AI-related tags from content"""
        try:
            prompt = f"""Extract 3-5 relevant AI/ML tags from this content:
            {content[:500]}
            
            Return only the tags as a comma-separated list."""
            
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "Extract relevant AI/ML tags from content."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=50,
                temperature=0.3
            )
            
            tags_str = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_str.split(',')]
            return tags[:5]
        except Exception as e:
            print(f"Error extracting tags: {e}")
            return []
