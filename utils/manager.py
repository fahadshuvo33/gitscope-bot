"""
Centralized utils manager for consistent usage across the project
"""
from templates import get_loading_message, get_error_message
from .keyboards import create_pagination_keyboard
from .error_handler import GitHubErrorHandler
from .formatting import _escape_markdown_v2
from . import git_api
import aiohttp

class GitHubAPIWrapper:
    """Wrapper for GitHub API with centralized access"""
    
    def __init__(self):
        self.error_handler = GitHubErrorHandler()
    
    async def get_user_profile(self, username):
        """Get user profile with error handling and logging"""
        try:
            async with aiohttp.ClientSession() as session:
                result = await git_api.fetch_user_info(session, username)
                
            return result
        except Exception as e:
            return None
    
    async def get_repository_info(self, repo_name):
        """Get repository info with error handling and logging"""
        try:
            async with aiohttp.ClientSession() as session:
                result = await git_api.fetch_repo_info(session, repo_name)
                
            return result
        except Exception as e:
            return None

class UtilsManager:
    """Central utils manager"""
    
    def __init__(self):
        self.github_api = GitHubAPIWrapper()
    
    def escape_markdown(self, text, version=2):
        """Escape markdown text"""
        return _escape_markdown_v2(text) if version == 2 else text
    
    def create_keyboard(self, base_callback, current_page, total_pages, back_callback, 
                       show_navigation=True, extra_buttons=None):
        """Create keyboard with pagination"""
        return create_pagination_keyboard(
            base_callback, current_page, total_pages, back_callback,
            show_navigation, extra_buttons
        )
    
    async def show_loading(self, message, content, action="Loading", keep_content=False):
        """Show loading animation"""
        return await show_static_loading(message, content, action, keep_content)
    
    async def handle_error(self, message, operation, exception=None, context="operation", 
                          username=None, keep_content=False):
        """Handle errors with logging"""
        error_msg = str(exception) if exception else "Unknown error"
        await show_error(message, f"Error in {context}: {error_msg}")

# Global utils instance
utils = UtilsManager()
