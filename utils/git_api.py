import os
import base64
import aiohttp
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitHub-Explorer-Bot/2.0"
}

# Add authorization header if token is provided
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# Configure logging
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL = 300  # 5 minutes cache TTL
_cache = {}

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""
    pass

class RateLimitError(GitHubAPIError):
    """Exception for rate limit exceeded"""
    def __init__(self, message: str, reset_time: Optional[int] = None):
        super().__init__(message)
        self.reset_time = reset_time

class NotFoundError(GitHubAPIError):
    """Exception for resource not found"""
    pass

class NetworkError(GitHubAPIError):
    """Exception for network-related issues"""
    pass

def _get_cache_key(path: str, params: Optional[Dict] = None) -> str:
    """Generate cache key from path and params"""
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{path}?{param_str}"
    return path

def _get_from_cache(key: str) -> Optional[Any]:
    """Get data from cache if not expired"""
    if key in _cache:
        data, timestamp = _cache[key]
        if datetime.now().timestamp() - timestamp < CACHE_TTL:
            logger.debug(f"Cache hit for: {key}")
            return data
        else:
            del _cache[key]
    return None

def _set_cache(key: str, data: Any):
    """Set data in cache with timestamp"""
    _cache[key] = (data, datetime.now().timestamp())
    # Cleanup old entries if cache is too large
    if len(_cache) > 100:
        # Remove oldest entries
        sorted_items = sorted(_cache.items(), key=lambda x: x[1][1])
        for old_key, _ in sorted_items[:20]:
            del _cache[old_key]

async def _make_request_with_retry(
    session: aiohttp.ClientSession,
    path: str,
    params: Optional[Dict] = None,
    timeout: int = 8,
    max_retries: int = 3,
    use_cache: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Optional[Dict]:
    """Make request with retry logic, caching, and better error handling"""
    url = f"{GITHUB_API_BASE}{path}"

    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(path, params)
        cached_data = _get_from_cache(cache_key)
        if cached_data:
            return cached_data

    for attempt in range(max_retries):
        try:
            if progress_callback and attempt > 0:
                progress_callback(f"Retry attempt {attempt + 1}/{max_retries}")

            # Create timeout configuration
            timeout_config = aiohttp.ClientTimeout(
                total=timeout,
                connect=5,  # Connection timeout
                sock_read=timeout - 2  # Socket read timeout
            )

            async with session.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=timeout_config,
                ssl=False  # Skip SSL verification if needed
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    # Cache successful responses
                    if use_cache:
                        _set_cache(cache_key, data)
                    return data

                elif response.status == 404:
                    logger.warning(f"GitHub API: Resource not found: {url}")
                    raise NotFoundError(f"Resource not found: {path}")

                elif response.status == 403:
                    # Extract rate limit info
                    remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    reset_time = response.headers.get('X-RateLimit-Reset')

                    if remaining == '0':
                        reset_timestamp = int(reset_time) if reset_time else None
                        logger.warning(f"GitHub API: Rate limit exceeded. Reset at: {reset_timestamp}")
                        raise RateLimitError("GitHub API rate limit exceeded", reset_timestamp)
                    else:
                        raise GitHubAPIError("Access denied")

                elif response.status == 401:
                    raise GitHubAPIError("Unauthorized access - check your GitHub token")

                elif response.status >= 500:
                    if attempt < max_retries - 1:
                        logger.warning(f"GitHub API: Server error {response.status}, retrying... (attempt {attempt + 1})")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise GitHubAPIError(f"GitHub server error: {response.status}")

                else:
                    error_text = await response.text()
                    logger.warning(f"GitHub API: Unexpected status {response.status}: {error_text}")
                    raise GitHubAPIError(f"Unexpected error: {response.status}")

        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                logger.warning(f"GitHub API: Request timeout, retrying... (attempt {attempt + 1})")
                await asyncio.sleep(1)
                continue
            logger.error(f"GitHub API: Request timeout after {max_retries} attempts: {url}")
            raise NetworkError("Request timeout - GitHub API is not responding")

        except aiohttp.ClientConnectorError as e:
            if attempt < max_retries - 1:
                logger.warning(f"GitHub API: Connection error, retrying... (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2)
                continue
            logger.error(f"GitHub API: Connection error after {max_retries} attempts: {e}")
            raise NetworkError("Connection error - check your internet connection")

        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                logger.warning(f"GitHub API: Client error, retrying... (attempt {attempt + 1}): {e}")
                await asyncio.sleep(1)
                continue
            logger.error(f"GitHub API: Client error after {max_retries} attempts: {e}")
            raise NetworkError(f"Network error: {str(e)}")

    # If we get here, all retries failed
    raise NetworkError(f"Failed to connect to GitHub API after {max_retries} attempts")

# Enhanced session factory
def create_github_session() -> aiohttp.ClientSession:
    """Create aiohttp session with optimized settings"""
    connector = aiohttp.TCPConnector(
        limit=10,  # Total connection limit
        limit_per_host=5,  # Per-host connection limit
        ttl_dns_cache=300,  # DNS cache TTL
        use_dns_cache=True,
        keepalive_timeout=30,
        enable_cleanup_closed=True,
        force_close=False,  # Reuse connections
    )

    timeout = aiohttp.ClientTimeout(
        total=10,
        connect=5
    )

    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={"User-Agent": "GitHub-Explorer-Bot/2.0"},
    )

# Main API functions
async def fetch_repo_info(session: aiohttp.ClientSession, repo: str) -> Optional[Dict]:
    """Fetch repository information from GitHub API"""
    repo = clean_repo_name(repo)
    if not repo:
        logger.error(f"Invalid repository format: {repo}")
        return None

    try:
        data = await _make_request_with_retry(session, f"/repos/{repo}", timeout=6)
        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch repo info for {repo}: {e}")
        return None

async def fetch_contributors(session: aiohttp.ClientSession, repo: str, limit: int = 10) -> Optional[List[Dict]]:
    """Fetch repository contributors with timeout handling"""
    repo = clean_repo_name(repo)
    if not repo:
        return None

    try:
        params = {"per_page": min(limit, 100)}
        data = await _make_request_with_retry(session, f"/repos/{repo}/contributors", params=params, timeout=6)
        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch contributors for {repo}: {e}")
        return None

async def fetch_releases(session: aiohttp.ClientSession, repo: str, limit: int = 5) -> Optional[List[Dict]]:
    """Fetch latest releases with better error handling"""
    repo = clean_repo_name(repo)
    if not repo:
        return None

    try:
        params = {"per_page": min(limit, 100)}
        data = await _make_request_with_retry(session, f"/repos/{repo}/releases", params=params, timeout=6)
        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch releases for {repo}: {e}")
        return None

async def fetch_open_prs(session: aiohttp.ClientSession, repo: str, limit: int = 10) -> Optional[List[Dict]]:
    """Fetch open pull requests with timeout handling"""
    repo = clean_repo_name(repo)
    if not repo:
        return None

    try:
        params = {
            "state": "open",
            "sort": "updated",
            "direction": "desc",
            "per_page": min(limit, 100)
        }
        data = await _make_request_with_retry(session, f"/repos/{repo}/pulls", params=params, timeout=6)
        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch open PRs for {repo}: {e}")
        return None

async def fetch_open_issues(session: aiohttp.ClientSession, repo: str, limit: int = 10) -> Optional[List[Dict]]:
    """Fetch open issues with timeout handling"""
    repo = clean_repo_name(repo)
    if not repo:
        return None

    try:
        params = {
            "state": "open",
            "sort": "updated",
            "direction": "desc",
            "per_page": min(limit, 100)
        }
        data = await _make_request_with_retry(session, f"/repos/{repo}/issues", params=params, timeout=6)

        # Filter out pull requests
        if data:
            issues_only = [issue for issue in data if 'pull_request' not in issue]
            return issues_only

        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch open issues for {repo}: {e}")
        return None

async def fetch_languages(session: aiohttp.ClientSession, repo: str) -> Optional[Dict[str, int]]:
    """Fetch programming languages with timeout handling"""
    repo = clean_repo_name(repo)
    if not repo:
        return None

    try:
        data = await _make_request_with_retry(session, f"/repos/{repo}/languages", timeout=6)
        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch languages for {repo}: {e}")
        return None

async def fetch_readme(session: aiohttp.ClientSession, repo: str) -> Optional[str]:
    """Fetch repository README with timeout handling"""
    repo = clean_repo_name(repo)
    if not repo:
        return None

    try:
        data = await _make_request_with_retry(session, f"/repos/{repo}/readme", timeout=6)

        if not data or "content" not in data:
            return None

        # Decode base64 content
        try:
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        except Exception as e:
            logger.error(f"Failed to decode README content for {repo}: {e}")
            return None

    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch README for {repo}: {e}")
        return None

async def fetch_user_info(session: aiohttp.ClientSession, username: str) -> Optional[Dict]:
    """Fetch user information with timeout handling"""
    if not username or not username.strip():
        return None

    try:
        username = username.strip()
        data = await _make_request_with_retry(session, f"/users/{username}", timeout=6)
        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch user info for {username}: {e}")
        return None

async def search_repositories(
    session: aiohttp.ClientSession,
    query: str,
    limit: int = 10,
    sort: str = 'stars'
) -> Optional[List[Dict]]:
    """Search for repositories with timeout handling"""
    if not query or not query.strip():
        return None

    try:
        params = {
            "q": query.strip(),
            "sort": sort,
            "order": "desc",
            "per_page": min(limit, 100)
        }

        data = await _make_request_with_retry(session, "/search/repositories", params=params, timeout=8)

        if data and 'items' in data:
            return data['items']

        return None

    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to search repositories for query '{query}': {e}")
        return None

# Additional API functions
async def fetch_user_repos(
    session: aiohttp.ClientSession,
    username: str,
    limit: int = 10,
    sort: str = "updated"
) -> Optional[List[Dict]]:
    """Fetch user's repositories"""
    if not username or not username.strip():
        return None

    try:
        params = {
            "sort": sort,
            "direction": "desc",
            "per_page": min(limit, 100)
        }
        data = await _make_request_with_retry(session, f"/users/{username}/repos", params=params, timeout=6)
        return data
    except (NotFoundError, NetworkError, GitHubAPIError) as e:
        logger.error(f"Failed to fetch repos for user {username}: {e}")
        return None

async def fetch_trending_repos(
    session: aiohttp.ClientSession,
    language: Optional[str] = None,
    since: str = "daily",
    limit: int = 10
) -> Optional[List[Dict]]:
    """Fetch trending repositories (uses search API as GitHub doesn't have official trending API)"""
    try:
        # Build query for trending repos
        query = "stars:>1"
        if language:
            query += f" language:{language}"

        # Add date filter based on 'since' parameter
        if since == "daily":
            date_filter = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif since == "weekly":
            date_filter = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        else:  # monthly
            date_filter = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        query += f" created:>{date_filter}"

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100)
        }

        data = await _make_request_with_retry(session, "/search/repositories", params=params, timeout=8)

        if data and 'items' in data:
            return data['items']

        return None
    except Exception as e:
        logger.error(f"Failed to fetch trending repos: {e}")
        return None

# Rate limit and validation functions
async def check_rate_limit(session: aiohttp.ClientSession) -> Optional[Dict]:
    """Check current rate limit status"""
    try:
        data = await _make_request_with_retry(session, "/rate_limit", use_cache=False)
        return data
    except Exception as e:
        logger.error(f"Failed to check rate limit: {e}")
        return None

async def validate_github_token(session: aiohttp.ClientSession) -> bool:
    """Validate if the GitHub token is valid"""
    try:
        data = await _make_request_with_retry(session, "/user", use_cache=False)
        return data is not None
    except GitHubAPIError:
        return False

# Batch operations
async def batch_fetch_repos(
    session: aiohttp.ClientSession,
    repo_names: List[str]
) -> List[Optional[Dict]]:
    """Fetch multiple repositories in parallel"""
    tasks = [fetch_repo_info(session, repo) for repo in repo_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to None
    return [None if isinstance(r, Exception) else r for r in results]

# Utility functions
def validate_repo_name(repo: str) -> bool:
    """Validate repository name format"""
    if not repo or not isinstance(repo, str):
        return False

    repo = repo.strip()
    if '/' not in repo:
        return False

    parts = repo.split('/')
    if len(parts) != 2:
        return False

    owner, name = parts

    if not owner or not name:
        return False

    # Check for invalid characters
    invalid_chars = ['<', '>', '"', '|', '*', '?', ':', '\\']
    if any(char in repo for char in invalid_chars):
        return False

    # Check length constraints
    if len(owner) > 39 or len(name) > 100:
        return False

    return True

def clean_repo_name(repo: str) -> Optional[str]:
    """Clean and normalize repository name"""
    if not repo:
        return None

    repo = repo.strip()

    # Remove common URL prefixes
    prefixes_to_remove = [
        'https://github.com/',
        'http://github.com/',
        'github.com/',
        'www.github.com/',
        'https://www.github.com/',
        'http://www.github.com/'
    ]

    for prefix in prefixes_to_remove:
        if repo.lower().startswith(prefix):
            repo = repo[len(prefix):]
            break

    # Remove .git suffix
    if repo.endswith('.git'):
        repo = repo[:-4]

    # Remove trailing slashes
    repo = repo.rstrip('/')

    # Extract owner/repo from path
    parts = repo.split('/')
    if len(parts) >= 2:
        repo = f"{parts[0]}/{parts[1]}"

    return repo if validate_repo_name(repo) else None

def parse_github_url(url: str) -> Optional[str]:
    """Extract repository name from various GitHub URL formats"""
    if not url:
        return None

    # Direct repo name
    if '/' in url and 'github.com' not in url:
        return clean_repo_name(url)

    # GitHub URLs
    return clean_repo_name(url)

# Cache management
def clear_cache():
    """Clear the API cache"""
    global _cache
    _cache = {}
    logger.info("API cache cleared")

def get_cache_info() -> Dict[str, Any]:
    """Get information about the cache"""
    return {
        "size": len(_cache),
        "entries": list(_cache.keys()),
        "memory_usage_bytes": sum(len(str(v[0])) for v in _cache.values())
    }

def get_rate_limit_info() -> Dict[str, str]:
    """Get human-readable rate limit info"""
    if GITHUB_TOKEN:
        return {
            "authenticated": "Yes",
            "limit": "5000 requests/hour",
            "search_limit": "30 requests/minute"
        }
    else:
        return {
            "authenticated": "No",
            "limit": "60 requests/hour",
            "search_limit": "10 requests/minute"
        }

# Error message helpers
def get_user_friendly_error_message(error: Exception) -> str:
    """Convert exception to user-friendly message"""
    if isinstance(error, NotFoundError):
        return "Repository or user not found. Please check the name and try again."
    elif isinstance(error, RateLimitError):
        return "GitHub API rate limit exceeded. Please try again later."
    elif isinstance(error, NetworkError):
        return "Network error. Please check your internet connection."
    elif isinstance(error, GitHubAPIError):
        if "Unauthorized" in str(error):
            return "Authentication failed. Please check your GitHub token."
        return f"GitHub API error: {str(error)}"
    else:
        return "An unexpected error occurred. Please try again."

# Initialize message
if not GITHUB_TOKEN:
    print("⚠️  No GitHub token found - using rate-limited requests (60/hour)")
    print("   To increase limits, add GITHUB_TOKEN to your .env file")
else:
    print("✅ GitHub token loaded - enhanced rate limit (5000/hour)")
