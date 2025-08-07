import os
import json
from typing import List, Dict, Optional
from datetime import datetime, date
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
        today = date.today().strftime('%Y-%m-%d')
        
        system_prompt = f"""You are a strict AI news curator. Extract ONLY articles that meet ALL criteria:
1. MUST be related to AI, machine learning, LLMs, or artificial intelligence
2. MUST be published TODAY ({today}) - look for date indicators like "today", "hours ago", or explicit date {today}
3. MUST have both a headline and a link
4. DO NOT include articles from previous days, even if they're recent

IMPORTANT: If an article has no clear date or the date is ambiguous, EXCLUDE it.
Only include articles you're confident were published today.

Return a JSON object with an 'articles' array containing objects with:
- headline: the article title
- link: absolute URL
- date: {today}
- confidence: 'high' if date is explicit, 'medium' if inferred from "today"/"hours ago"

Example: {{"articles": [{{"headline": "...", "link": "...", "date": "{today}", "confidence": "high"}}]}}"""

        user_prompt = f"""Extract AI-related articles from this content:
Source URL: {source_url}
Content:
{markdown_content}"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
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
                model="gpt-4o",
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
                model="gpt-4o",
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