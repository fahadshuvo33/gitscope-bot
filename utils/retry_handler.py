import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from typing import Callable, Any, List, Type, Optional, Dict
from telegram.error import NetworkError, TimedOut
import aiohttp
import requests

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#                    SMART RETRY SYSTEM WITH ENHANCEMENTS
# ═══════════════════════════════════════════════════════════════════


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_backoff: bool = True,
        jitter: bool = True,
        jitter_factor: float = 0.2,
        retryable_errors: List[Type[Exception]] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.jitter = jitter
        self.jitter_factor = jitter_factor
        self.retryable_errors = retryable_errors or [
            NetworkError,
            TimedOut,
            ConnectionError,
            aiohttp.ClientError,
            aiohttp.ServerTimeoutError,
            requests.ConnectionError,
            requests.Timeout,
            OSError,  # For DNS and network issues
        ]


class RetryContext:
    """Context information for retry operations"""
    
    def __init__(self, endpoint: str = None, operation: str = None):
        self.endpoint = endpoint
        self.operation = operation
        self.start_time = time.time()
        self.attempts = []
    
    def record_attempt(self, attempt: int, exception: Exception = None, success: bool = False):
        self.attempts.append({
            'attempt': attempt,
            'timestamp': time.time(),
            'exception': str(exception) if exception else None,
            'exception_type': type(exception).__name__ if exception else None,
            'success': success
        })
    
    def get_total_time(self) -> float:
        return time.time() - self.start_time
    
    def get_summary(self) -> Dict:
        return {
            'total_attempts': len(self.attempts),
            'total_time': self.get_total_time(),
            'endpoint': self.endpoint,
            'operation': self.operation,
            'attempts': self.attempts
        }


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.breakers = defaultdict(lambda: {'failures': 0, 'last_failure': None, 'consecutive_failures': 0})
    
    def is_open(self, endpoint: str) -> bool:
        """Check if circuit is open (failing)"""
        breaker = self.breakers[endpoint]
        if breaker['consecutive_failures'] >= self.failure_threshold:
            if breaker['last_failure']:
                time_since_failure = (datetime.now() - breaker['last_failure']).seconds
                if time_since_failure < self.timeout:
                    return True
                else:
                    # Half-open state - allow one request through
                    logger.info(f"Circuit breaker half-open for {endpoint}")
                    breaker['consecutive_failures'] = self.failure_threshold - 1
        return False
    
    def record_success(self, endpoint: str):
        """Record successful request"""
        self.breakers[endpoint] = {'failures': 0, 'last_failure': None, 'consecutive_failures': 0}
        logger.debug(f"Circuit breaker reset for {endpoint}")
    
    def record_failure(self, endpoint: str):
        """Record failed request"""
        breaker = self.breakers[endpoint]
        breaker['failures'] += 1
        breaker['consecutive_failures'] += 1
        breaker['last_failure'] = datetime.now()
        
        if breaker['consecutive_failures'] == self.failure_threshold:
            logger.warning(f"Circuit breaker opened for {endpoint}")


class RetryHandler:
    """Smart retry handler with circuit breaker and enhanced features"""

    def __init__(self):
        # Different configs for different scenarios
        self.configs = {
            "network": RetryConfig(
                max_attempts=3, 
                base_delay=1.0,
                jitter=True
            ),
            "api": RetryConfig(
                max_attempts=2, 
                base_delay=2.0,
                jitter=True
            ),
            "rate_limit": RetryConfig(
                max_attempts=1, 
                base_delay=60.0,
                jitter=True,
                jitter_factor=0.1  # Less jitter for rate limits
            ),
        }
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker()
        
        # Stats tracking
        self.stats = defaultdict(lambda: {'success': 0, 'failure': 0, 'total_time': 0})

    def should_retry(self, exception: Exception, attempt: int, max_attempts: int) -> tuple[bool, Optional[float]]:
        """
        Determine if we should retry based on exception type
        Returns: (should_retry, optional_wait_time)
        """
        if attempt >= max_attempts:
            return False, None

        exception_str = str(exception).lower()

        # Always retry network/connection issues
        if isinstance(exception, (NetworkError, TimedOut, ConnectionError, OSError)):
            return True, None

        # Retry aiohttp errors
        if isinstance(exception, (aiohttp.ClientError, aiohttp.ServerTimeoutError)):
            return True, None

        # Retry requests errors
        if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
            return True, None

        # Handle GitHub's specific rate limit response
        if hasattr(exception, 'response'):
            response = exception.response
            if response and hasattr(response, 'headers'):
                if response.status_code == 403:
                    remaining = response.headers.get('X-RateLimit-Remaining', '1')
                    if remaining == '0':
                        reset_time = response.headers.get('X-RateLimit-Reset')
                        if reset_time:
                            wait_time = int(reset_time) - int(time.time())
                            if 0 < wait_time < 300:  # Max 5 min wait
                                return True, wait_time
                        return True, 60  # Default 60s wait for rate limit

        # Retry server errors (5xx)
        if any(code in exception_str for code in ["500", "502", "503", "504"]):
            return True, None

        # Retry timeouts
        if "timeout" in exception_str or "timed out" in exception_str:
            return True, None

        # DON'T retry client errors (4xx except rate limit)
        if any(code in exception_str for code in ["400", "401", "404", "422"]):
            return False, None

        # Special handling for rate limits
        if "403" in exception_str and "rate" in exception_str:
            return attempt == 1, 60  # Only retry once for rate limits

        # Default: don't retry unknown errors
        return False, None

    def get_retry_delay(self, attempt: int, config: RetryConfig, exception: Exception = None, override_delay: float = None) -> float:
        """Calculate delay before next retry with optional jitter"""
        # Use override delay if provided (e.g., from rate limit headers)
        if override_delay is not None:
            base_delay = override_delay
        elif exception and "403" in str(exception).lower() and "rate" in str(exception).lower():
            base_delay = 60.0  # Default rate limit delay
        elif config.exponential_backoff:
            base_delay = config.base_delay * (2 ** (attempt - 1))
            base_delay = min(base_delay, config.max_delay)
        else:
            base_delay = config.base_delay
        
        # Add jitter if enabled
        if config.jitter:
            jitter = base_delay * config.jitter_factor * random.random()
            return base_delay + jitter
        
        return base_delay

    async def retry_with_callback(
        self,
        func: Callable,
        config_type: str = "network",
        retry_callback: Callable = None,
        context: RetryContext = None,
        *args,
        **kwargs,
    ):
        """
        Execute function with retry logic and optional callback for retry notifications

        Args:
            func: The async function to retry
            config_type: 'network', 'api', or 'rate_limit'
            retry_callback: Called on each retry attempt (for updating UI)
            context: Retry context for tracking
            *args, **kwargs: Arguments for the function
        """
        config = self.configs.get(config_type, self.configs["network"])
        last_exception = None
        context = context or RetryContext(operation=func.__name__)
        
        # Check circuit breaker
        if context.endpoint and self.circuit_breaker.is_open(context.endpoint):
            raise ConnectionError(f"Circuit breaker open for {context.endpoint}")
        
        start_time = time.time()

        for attempt in range(1, config.max_attempts + 1):
            try:
                logger.debug(f"Attempt {attempt}/{config.max_attempts} for {context.operation}")
                
                result = await func(*args, **kwargs)
                
                # Record success
                context.record_attempt(attempt, success=True)
                if context.endpoint:
                    self.circuit_breaker.record_success(context.endpoint)
                
                # Update stats
                operation = context.operation or func.__name__
                self.stats[operation]['success'] += 1
                self.stats[operation]['total_time'] += time.time() - start_time
                
                if attempt > 1:
                    logger.info(
                        f"Succeeded after {attempt} attempts "
                        f"(total time: {context.get_total_time():.2f}s)"
                    )
                
                return result

            except Exception as e:
                last_exception = e
                context.record_attempt(attempt, e)
                logger.warning(f"Attempt {attempt} failed: {type(e).__name__}: {str(e)}")

                should_retry, override_delay = self.should_retry(e, attempt, config.max_attempts)
                
                if not should_retry:
                    logger.error(f"Not retrying {type(e).__name__}: {str(e)}")
                    break

                if attempt < config.max_attempts:
                    delay = self.get_retry_delay(attempt, config, e, override_delay)
                    logger.info(
                        f"Retrying in {delay:.1f}s... "
                        f"(attempt {attempt + 1}/{config.max_attempts})"
                    )

                    # Notify UI about retry
                    if retry_callback:
                        await retry_callback(attempt + 1, config.max_attempts, delay)

                    await asyncio.sleep(delay)

        # All retries failed
        if context.endpoint:
            self.circuit_breaker.record_failure(context.endpoint)
        
        # Update failure stats
        operation = context.operation or func.__name__
        self.stats[operation]['failure'] += 1
        self.stats[operation]['total_time'] += time.time() - start_time
        
        # Log final failure with context
        logger.error(
            f"All retry attempts failed for {context.operation}: "
            f"{context.get_summary()}"
        )
        
        raise last_exception

    def sync_retry(self, func: Callable, config_type: str = "network", 
                   context: RetryContext = None, *args, **kwargs):
        """Synchronous version of retry for non-async functions"""
        config = self.configs.get(config_type, self.configs["network"])
        last_exception = None
        context = context or RetryContext(operation=func.__name__)
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                context.record_attempt(attempt, success=True)
                return result
            except Exception as e:
                last_exception = e
                context.record_attempt(attempt, e)
                
                should_retry, override_delay = self.should_retry(e, attempt, config.max_attempts)
                if not should_retry:
                    raise
                
                if attempt < config.max_attempts:
                    delay = self.get_retry_delay(attempt, config, e, override_delay)
                    time.sleep(delay)
        
        raise last_exception

    def get_stats(self, operation: str = None) -> Dict:
        """Get retry statistics"""
        if operation:
            return dict(self.stats[operation])
        return dict(self.stats)

    def reset_stats(self, operation: str = None):
        """Reset statistics"""
        if operation:
            self.stats[operation] = {'success': 0, 'failure': 0, 'total_time': 0}
        else:
            self.stats.clear()


# Global retry handler instance
retry_handler = RetryHandler()

# ═══════════════════════════════════════════════════════════════════
#                    RETRY DECORATORS
# ═══════════════════════════════════════════════════════════════════


def retry_on_failure(config_type: str = "network", context: RetryContext = None):
    """Decorator for automatic retry with context"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            ctx = context or RetryContext(operation=func.__name__)
            return await retry_handler.retry_with_callback(
                func, config_type, None, ctx, *args, **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            ctx = context or RetryContext(operation=func.__name__)
            return retry_handler.sync_retry(
                func, config_type, ctx, *args, **kwargs
            )
        
        # Return appropriate wrapper based on function type
                # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience decorators
retry_network = retry_on_failure("network")
retry_api = retry_on_failure("api") 
retry_rate_limit = retry_on_failure("rate_limit")


# ═══════════════════════════════════════════════════════════════════
#                    USAGE HELPERS
# ═══════════════════════════════════════════════════════════════════

async def with_retry_notification(
    func: Callable,
    message,
    config_type: str = "network",
    context: RetryContext = None,
    *args,
    **kwargs
):
    """
    Execute function with retry and update Telegram message on retries
    
    Args:
        func: Function to retry
        message: Telegram message object to update
        config_type: Type of retry configuration
        context: Optional retry context
        *args, **kwargs: Arguments for func
    """
    
    async def update_message_callback(attempt: int, max_attempts: int, delay: float):
        """Update Telegram message during retry"""
        try:
            retry_text = (
                f"⏳ Retry {attempt}/{max_attempts} in {delay:.0f}s...\n"
                f"Please wait while we reconnect."
            )
            await message.edit_text(retry_text, parse_mode="Markdown")
        except:
            pass  # Ignore errors when updating message
    
    return await retry_handler.retry_with_callback(
        func,
        config_type,
        update_message_callback,
        context,
        *args,
        **kwargs
    )


def create_retry_context(endpoint: str = None, operation: str = None) -> RetryContext:
    """Create a retry context for tracking"""
    return RetryContext(endpoint=endpoint, operation=operation)


# ═══════════════════════════════════════════════════════════════════
#                    EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════

"""
# Basic usage with decorator
@retry_api
async def fetch_github_data(repo_name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.github.com/repos/{repo_name}") as response:
            return await response.json()

# Advanced usage with context and UI updates
async def fetch_with_ui_update(message, repo_name: str):
    context = create_retry_context(
        endpoint="github_api",
        operation="fetch_repo"
    )
    
    async def fetch_data():
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/repos/{repo_name}") as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                return await response.json()
    
    return await with_retry_notification(
        fetch_data,
        message,
        "api",
        context
    )

# Synchronous function with retry
@retry_network
def download_file(url: str) -> bytes:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content

# Manual retry with custom config
async def custom_retry_example():
    # Create custom config
    custom_config = RetryConfig(
        max_attempts=5,
        base_delay=0.5,
        max_delay=30,
        jitter_factor=0.3
    )
    
    # Add to handler
    retry_handler.configs["custom"] = custom_config
    
    @retry_on_failure("custom")
    async def unstable_operation():
        # Your code here
        pass
    
    return await unstable_operation()

# Get statistics
def print_retry_stats():
    stats = retry_handler.get_stats()
    for operation, data in stats.items():
        success_rate = data['success'] / (data['success'] + data['failure']) * 100 if data['success'] + data['failure'] > 0 else 0
        avg_time = data['total_time'] / (data['success'] + data['failure']) if data['success'] + data['failure'] > 0 else 0
        print(f"{operation}: {success_rate:.1f}% success, avg time: {avg_time:.2f}s")

# Circuit breaker status
def check_circuit_status(endpoint: str) -> bool:
    return retry_handler.circuit_breaker.is_open(endpoint)
"""

# ═══════════════════════════════════════════════════════════════════
#                    INTEGRATION WITH TRENDING BOT
# ═══════════════════════════════════════════════════════════════════

async def github_api_with_retry(url: str, params: dict = None, headers: dict = None):
    """
    GitHub API wrapper with automatic retry and circuit breaker
    
    Usage in your trending bot:
    
    # Replace this:
    async with session.get(GITHUB_API_URL, headers=HEADERS, params=params) as response:
        data = await response.json()
    
    # With this:
    data = await github_api_with_retry(GITHUB_API_URL, params=params, headers=HEADERS)
    """
    context = create_retry_context(
        endpoint="github_search_api",
        operation="search_repositories"
    )
    
    @retry_api
    async def make_request():
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                # Check for rate limiting
                if response.status == 403:
                    remaining = response.headers.get('X-RateLimit-Remaining', '1')
                    if remaining == '0':
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        current_time = int(time.time())
                        wait_time = reset_time - current_time
                        
                        error = aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
                        error.response = response
                        raise error
                
                # Handle other non-200 responses
                if response.status != 200:
                    text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=text
                    )
                
                return await response.json()
    
    return await retry_handler.retry_with_callback(
        make_request,
        "api",
        None,
        context
    )


# ═══════════════════════════════════════════════════════════════════
#                    MONITORING AND HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════════

class RetryMonitor:
    """Monitor retry handler health and performance"""
    
    @staticmethod
    def get_health_status() -> Dict:
        """Get overall health status of retry system"""
        stats = retry_handler.get_stats()
        circuit_breakers = retry_handler.circuit_breaker.breakers
        
        total_requests = sum(s['success'] + s['failure'] for s in stats.values())
        total_failures = sum(s['failure'] for s in stats.values())
        failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
        
        open_circuits = [
            endpoint for endpoint, breaker in circuit_breakers.items()
            if retry_handler.circuit_breaker.is_open(endpoint)
        ]
        
        return {
            'status': 'healthy' if failure_rate < 50 and not open_circuits else 'degraded',
            'total_requests': total_requests,
            'failure_rate': f"{failure_rate:.1f}%",
            'open_circuits': open_circuits,
            'stats': stats
        }
    
    @staticmethod
    def log_health_status():
        """Log current health status"""
        health = RetryMonitor.get_health_status()
        logger.info(f"Retry Handler Health: {health['status']}, "
                   f"Failure Rate: {health['failure_rate']}, "
                   f"Open Circuits: {len(health['open_circuits'])}")


# Create monitor instance
retry_monitor = RetryMonitor()

# ═══════════════════════════════════════════════════════════════════
#                    EXPORT ALL PUBLIC COMPONENTS
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    # Main components
    'RetryHandler',
    'RetryConfig',
    'RetryContext',
    'CircuitBreaker',
    
    # Global instances
    'retry_handler',
    'retry_monitor',
    
    # Decorators
    'retry_on_failure',
    'retry_network',
    'retry_api',
    'retry_rate_limit',
    
    # Helper functions
    'with_retry_notification',
    'create_retry_context',
    'github_api_with_retry',
    
    # Monitoring
    'RetryMonitor'
]