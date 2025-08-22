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
                temperature=0.5,
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
                max_tokens=2000
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
                temperature=0.5,
                max_tokens=max_tokens
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
                max_tokens=1000,
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
                max_tokens=500,
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
                temperature=0.5,
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
                max_tokens=50,
                temperature=0.3
            )
            
            tags_str = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_str.split(',')]
            return tags[:5]
        except Exception as e:
            print(f"Error extracting tags: {e}")
            return []
