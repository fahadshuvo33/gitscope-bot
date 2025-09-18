# trending/__init__.py
"""Trending module initialization"""

from .handlers import show_languages_menu, register_trending_handlers
from .api import fetch_trending_repos

__all__ = [
    'show_languages_menu',
    'register_trending_handlers',
    'fetch_trending_repos'
]