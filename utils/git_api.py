import os
import base64
import aiohttp
import logging
import asyncio
from datetime import datetime, timedelta
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

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""
    pass

class RateLimitError(GitHubAPIError):
    """Exception for rate limit exceeded"""
    pass

class NotFoundError(GitHubAPIError):
    """Exception for resource not found"""
    pass

class NetworkError(GitHubAPIError):
    """Exception for network-related issues"""
    pass

async def _make_request_with_retry(session, path, params=None, timeout=8, max_retries=3):
    """Make request with retry logic and better error handling"""
    url = f"{GITHUB_API_BASE}{path}"

    for attempt in range(max_retries):
        try:
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
                    return await response.json()

                elif response.status == 404:
                    logger.warning(f"GitHub API: Resource not found: {url}")
                    raise NotFoundError(f"Resource not found: {path}")

                elif response.status == 403:
                    if 'X-RateLimit-Remaining' in response.headers:
                        remaining = response.headers.get('X-RateLimit-Remaining', '0')
                        logger.warning(f"GitHub API: Rate limit exceeded. Remaining: {remaining}")
                        raise RateLimitError("GitHub API rate limit exceeded")
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

# Create session factory with better configuration
def create_github_session():
    """Create aiohttp session with optimized settings"""
    connector = aiohttp.TCPConnector(
        limit=10,  # Total connection limit
        limit_per_host=5,  # Per-host connection limit
        ttl_dns_cache=300,  # DNS cache TTL
        use_dns_cache=True,
        keepalive_timeout=30,
        enable_cleanup_closed=True
    )

    timeout = aiohttp.ClientTimeout(
        total=10,
        connect=5
    )

    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={"User-Agent": "GitHub-Explorer-Bot/2.0"}
    )

# Update all existing functions to use the new retry mechanism
async def fetch_repo_info(session, repo):
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

async def fetch_contributors(session, repo, limit=10):
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

async def fetch_releases(session, repo, limit=5):
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

async def fetch_open_prs(session, repo, limit=10):
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

async def fetch_open_issues(session, repo, limit=10):
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

async def fetch_languages(session, repo):
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

async def fetch_readme(session, repo):
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

async def fetch_user_info(session, username):
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

async def search_repositories(session, query, limit=10, sort='stars'):
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

# Keep all other utility functions the same (validate_repo_name, clean_repo_name, etc.)
def validate_repo_name(repo):
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

    invalid_chars = ['<', '>', '"', '|', '*', '?', ':']
    if any(char in repo for char in invalid_chars):
        return False

    return True

def clean_repo_name(repo):
    """Clean and normalize repository name"""
    if not repo:
        return None

    repo = repo.strip().lower()

    prefixes_to_remove = [
        'https://github.com/',
        'http://github.com/',
        'github.com/',
        'www.github.com/'
    ]

    for prefix in prefixes_to_remove:
        if repo.startswith(prefix):
            repo = repo[len(prefix):]
            break

    if repo.endswith('.git'):
        repo = repo[:-4]

    repo = repo.rstrip('/')

    parts = repo.split('/')
    if len(parts) >= 2:
        repo = f"{parts[0]}/{parts[1]}"

    return repo if validate_repo_name(repo) else None

# Show warning if no token
if not GITHUB_TOKEN:
    print("⚠️  No GitHub token found - using rate-limited requests (60/hour)")
