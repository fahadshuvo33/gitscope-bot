# trending/api.py
"""API functions for fetching trending repositories"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import aiohttp

from utils.git_api import _make_request_with_retry
from .languages import get_language

logger = logging.getLogger(__name__)

async def fetch_trending_repos(
    session: aiohttp.ClientSession,
    language: Optional[str] = None,
    since: str = "weekly",
    limit: int = 10
) -> Optional[List[Dict]]:
    """Fetch trending repositories from GitHub"""
    try:
        # Build search query
        query_parts = []
        
        # Add language filter
        if language and language != "all":
            lang_info = get_language(language)
            github_lang = lang_info.get("github_name", language)
            query_parts.append(f'language:{github_lang}')
        
        # Add date filter
        date_map = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }
        days = date_map.get(since, 7)
        date_filter = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query_parts.append(f"created:>{date_filter}")
        
        # Ensure some minimum quality
        query_parts.append("stars:>10")
        
        # Build final query
        query = " ".join(query_parts) if query_parts else "stars:>100"
        
        logger.info(f"Search query: {query}")
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        # Make API request
        data = await _make_request_with_retry(
            session,
            "/search/repositories",
            params=params,
            timeout=10
        )
        
        if data and 'items' in data:
            logger.info(f"Found {len(data['items'])} repositories")
            return data['items'][:limit]
        
        logger.warning("No data returned from API")
        return None
        
    except Exception as e:
        logger.error(f"Error in fetch_trending_repos: {e}", exc_info=True)
        return None