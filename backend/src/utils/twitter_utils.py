"""
Utility functions for Twitter/X URL and handle parsing
"""

import re
from typing import Optional, Tuple


def parse_twitter_input(input_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse Twitter input to extract username and optional display name
    
    Accepts:
    - Twitter URLs: https://twitter.com/username, https://x.com/username
    - Handles: @username or username
    - With display name: "username:Display Name" or "@username:Display Name"
    
    Args:
        input_str: Input string (URL, handle, or handle:name format)
        
    Returns:
        Tuple of (username, display_name) where display_name may be None
    """
    if not input_str:
        return None, None
    
    input_str = input_str.strip()
    
    # First check if it's a URL (URLs can contain colons)
    if input_str.startswith(('http://', 'https://')):
        username = extract_username(input_str)
        return username, None
    
    # Check if input contains display name (format: "username:Display Name")
    if ':' in input_str:
        parts = input_str.split(':', 1)
        username_part = parts[0].strip()
        display_name = parts[1].strip() if len(parts) > 1 else None
        username = extract_username(username_part)
        return username, display_name
    
    # Extract username only
    username = extract_username(input_str)
    return username, None


def extract_username(input_str: str) -> Optional[str]:
    """
    Extract Twitter username from various input formats
    
    Args:
        input_str: URL or handle string
        
    Returns:
        Clean username without @ symbol, or None if invalid
    """
    if not input_str:
        return None
    
    input_str = input_str.strip()
    
    # Pattern for Twitter/X URLs - fixed to properly capture the full URL
    url_patterns = [
        r'^https?://(?:www\.)?twitter\.com/(@?[\w]+)/?.*$',
        r'^https?://(?:www\.)?x\.com/(@?[\w]+)/?.*$',
        r'^https?://(?:mobile\.)?twitter\.com/(@?[\w]+)/?.*$',
        r'^https?://(?:mobile\.)?x\.com/(@?[\w]+)/?.*$',
    ]
    
    # Try to match URL patterns
    for pattern in url_patterns:
        match = re.match(pattern, input_str, re.IGNORECASE)
        if match:
            username = match.group(1)
            # Remove @ if present and return
            return username.lstrip('@')
    
    # Not a URL, treat as handle
    # Remove @ symbol if present
    username = input_str.lstrip('@')
    
    # Validate username (Twitter rules: alphanumeric and underscore, max 15 chars)
    if re.match(r'^[\w]{1,15}$', username):
        return username
    
    return None


def format_twitter_url(username: str) -> str:
    """
    Format a clean Twitter URL from username
    
    Args:
        username: Twitter username (with or without @)
        
    Returns:
        Formatted Twitter URL
    """
    username = username.lstrip('@')
    return f"https://twitter.com/{username}"


def validate_twitter_username(username: str) -> bool:
    """
    Validate if a username follows Twitter's rules
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not username:
        return False
    
    username = username.lstrip('@')
    
    # Twitter username rules:
    # - 1-15 characters
    # - Only letters, numbers, and underscores
    return bool(re.match(r'^[\w]{1,15}$', username))


def parse_twitter_batch(input_list: list) -> list:
    """
    Parse a batch of Twitter inputs
    
    Args:
        input_list: List of URLs, handles, or handle:name formats
        
    Returns:
        List of tuples (username, display_name)
    """
    results = []
    for item in input_list:
        username, display_name = parse_twitter_input(item)
        if username:
            results.append((username, display_name))
    return results