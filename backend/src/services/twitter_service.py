"""
Twitter/X API Service for fetching tweets from targeted accounts
Uses twitterapi.io API service for reliable Twitter data access
"""

import os
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class TwitterService:
    """Service for interacting with Twitter/X via twitterapi.io API"""
    
    def __init__(self):
        api_key = os.getenv('TWITTER_API_KEY')
        if not api_key:
            raise ValueError("TWITTER_API_KEY must be set in environment variables")
        
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io"
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    async def fetch_user_tweets(
        self, 
        username: str, 
        limit: int = 50, 
        include_replies: bool = False
    ) -> List[Dict]:
        """
        Fetch latest tweets from a Twitter user
        
        Args:
            username: Twitter username (without @)
            limit: Maximum number of tweets to fetch
            include_replies: Whether to include replies
            
        Returns:
            List of processed tweet dictionaries
        """
        all_tweets = []
        cursor = ""
        
        async with aiohttp.ClientSession() as session:
            while len(all_tweets) < limit:
                try:
                    # Fetch batch of tweets
                    response_data = await self._fetch_tweet_batch(
                        session, username, cursor, include_replies
                    )
                    
                    if not response_data or response_data.get("status") != "success":
                        logger.error(f"Failed to fetch tweets for @{username}: {response_data}")
                        break
                    
                    # Extract and filter tweets
                    data = response_data.get("data", {})
                    tweets = data.get("tweets", [])
                    
                    if not tweets:
                        break
                    
                    # Filter out retweets and non-original content
                    filtered_tweets = self._filter_original_tweets(tweets)
                    
                    # Add filtered tweets up to limit
                    remaining = limit - len(all_tweets)
                    all_tweets.extend(filtered_tweets[:remaining])
                    
                    # Check if we've collected enough tweets
                    if len(all_tweets) >= limit:
                        break
                    
                    # Check for next page
                    has_next_page = data.get("has_next_page", False)
                    if not has_next_page:
                        break
                    
                    cursor = data.get("next_cursor", "")
                    
                    # Rate limiting - small delay between requests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error fetching tweets for @{username}: {str(e)}")
                    break
        
        return self._process_tweets_for_storage(all_tweets, username)
    
    async def _fetch_tweet_batch(
        self, 
        session: aiohttp.ClientSession,
        username: str, 
        cursor: str = "", 
        include_replies: bool = False
    ) -> Optional[Dict]:
        """
        Fetch a single batch of tweets from the API
        """
        endpoint = f"{self.base_url}/twitter/user/last_tweets"
        params = {
            "userName": username,
            "cursor": cursor,
            "includeReplies": str(include_replies).lower()  # Convert boolean to string
        }
        
        try:
            async with session.get(
                endpoint, 
                headers=self.headers, 
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed with status {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching tweets for @{username}")
            return None
        except Exception as e:
            logger.error(f"Error in API request: {str(e)}")
            return None
    
    def _filter_original_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """
        Filter tweets to only include original content from the author
        """
        filtered = []
        
        for tweet in tweets:
            tweet_text = tweet.get("text", "")
            
            # Skip retweets
            if tweet_text.startswith("RT @"):
                continue
            
            # Skip if marked as retweet
            if tweet.get("is_retweet", False):
                continue
            
            # Skip replies (tweets starting with @)
            if tweet.get("in_reply_to_status_id") or tweet_text.startswith("@"):
                continue
            
            # Skip quote tweets with minimal content
            if tweet.get("quoted_tweet"):
                # If it's mostly just a link or very short, skip it
                clean_text = tweet_text.strip()
                if clean_text.startswith("https://") or len(clean_text) < 50:
                    if clean_text.count(" ") < 5:
                        continue
            
            filtered.append(tweet)
        
        return filtered
    
    def _process_tweets_for_storage(
        self, 
        tweets: List[Dict], 
        username: str
    ) -> List[Dict]:
        """
        Process tweets into format suitable for storage in tweets table
        """
        processed = []
        
        for tweet in tweets:
            try:
                # Parse tweet date - handle Twitter date format
                created_at = tweet.get("createdAt", "")
                if created_at:
                    try:
                        # Try ISO format first
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except ValueError:
                        # Fall back to Twitter's date format
                        from datetime import datetime as dt_parser
                        dt = dt_parser.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                    published_at = dt.isoformat()
                else:
                    published_at = datetime.now().isoformat()
                
                # Extract tweet content
                text = tweet.get("text", "")
                
                # Extract media URLs
                media_urls = []
                media = tweet.get("media", [])
                for m in media:
                    if m.get("url"):
                        media_urls.append(m["url"])
                
                # Extract hashtags
                hashtags = []
                entities = tweet.get("entities", {})
                for hashtag in entities.get("hashtags", []):
                    hashtags.append(hashtag.get("text", ""))
                
                # Extract mentions
                mentions = []
                for mention in entities.get("mentions", []):
                    mentions.append(mention.get("username", ""))
                
                # Extract URLs
                urls = []
                for url in entities.get("urls", []):
                    urls.append(url.get("expanded_url", url.get("url", "")))
                
                # Build the processed tweet for tweets table
                processed_tweet = {
                    "tweet_id": tweet.get("id"),
                    "author_username": username,
                    "content": text,
                    "published_at": published_at,
                    "like_count": tweet.get("likeCount", 0),
                    "retweet_count": tweet.get("retweetCount", 0),
                    "reply_count": tweet.get("replyCount", 0),
                    "view_count": tweet.get("viewCount", 0),
                    "bookmark_count": tweet.get("bookmarkCount", 0),
                    
                    # Metadata
                    "is_reply": bool(tweet.get("in_reply_to_status_id")),
                    "is_retweet": text.startswith("RT @"),
                    "is_quote_tweet": bool(tweet.get("quoted_tweet")),
                    "has_media": len(media_urls) > 0,
                    "media_urls": media_urls,
                    "hashtags": hashtags,
                    "mentions": mentions,
                    "urls": urls,
                    
                    # Thread info
                    "conversation_id": tweet.get("conversation_id"),
                    "in_reply_to_tweet_id": tweet.get("in_reply_to_status_id"),
                    "quoted_tweet_id": tweet.get("quoted_tweet", {}).get("id") if tweet.get("quoted_tweet") else None,
                }
                
                # Add quoted tweet info if exists
                if tweet.get("quoted_tweet"):
                    quoted = tweet["quoted_tweet"]
                    quoted_author = quoted.get("author", {})
                    processed_tweet["quoted_tweet_content"] = quoted.get("text", "")[:500]
                    processed_tweet["quoted_tweet_author"] = quoted_author.get("userName", "Unknown")
                
                processed.append(processed_tweet)
                
            except Exception as e:
                logger.error(f"Error processing tweet {tweet.get('id')}: {str(e)}")
                continue
        
        return processed
    
    def _process_tweets_for_articles(
        self, 
        tweets: List[Dict], 
        username: str
    ) -> List[Dict]:
        """
        Process tweets into format suitable for storage as articles (backward compatibility)
        """
        processed = []
        
        for tweet in tweets:
            try:
                # Parse tweet date
                created_at = tweet.get("createdAt", "")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except ValueError:
                        from datetime import datetime as dt_parser
                        dt = dt_parser.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                    published_date = dt.date().isoformat()
                else:
                    published_date = date.today().isoformat()
                
                text = tweet.get("text", "")
                headline = text[:100] + "..." if len(text) > 100 else text
                headline = headline.replace("\n", " ").strip()
                
                # Format for articles table (backward compatibility)
                processed_tweet = {
                    "tweet_id": tweet.get("id"),
                    "author_username": username,
                    "headline": f"@{username}: {headline}",
                    "full_content": text,
                    "url": tweet.get("url", f"https://twitter.com/{username}/status/{tweet.get('id')}"),
                    "published_at": published_date,
                    "like_count": tweet.get("likeCount", 0),
                    "retweet_count": tweet.get("retweetCount", 0),
                    "reply_count": tweet.get("replyCount", 0),
                    "source_type": "twitter"
                }
                
                processed.append(processed_tweet)
                
            except Exception as e:
                logger.error(f"Error processing tweet for articles: {str(e)}")
                continue
        
        return processed
    
    async def fetch_tweets_for_date(
        self, 
        username: str, 
        target_date: date,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch tweets from a specific date
        
        Args:
            username: Twitter username (without @)
            target_date: Date to filter tweets
            limit: Maximum number of tweets to check
            
        Returns:
            List of tweets from the target date
        """
        # Fetch more tweets than needed to ensure we get all from target date
        all_tweets = await self.fetch_user_tweets(username, limit=limit)
        
        # Filter for target date
        target_date_str = target_date.isoformat()
        filtered_tweets = [
            tweet for tweet in all_tweets 
            if tweet.get("published_at") == target_date_str
        ]
        
        logger.info(f"Found {len(filtered_tweets)} tweets from @{username} on {target_date_str}")
        
        return filtered_tweets
    
    async def fetch_yesterday_tweets(self, username: str) -> List[Dict]:
        """
        Convenience method to fetch yesterday's tweets
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            List of yesterday's tweets
        """
        yesterday = date.today() - timedelta(days=1)
        return await self.fetch_tweets_for_date(username, yesterday)