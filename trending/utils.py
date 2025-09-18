# trending/utils.py
"""Utility functions for trending module"""
from typing import Optional

# Store user preferences
user_preferences = {}

def get_user_period(user_id: int) -> str:
    """Get user's selected time period"""
    return user_preferences.get(user_id, {}).get("period", "weekly")

def set_user_period(user_id: int, period: str):
    """Set user's selected time period"""
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    user_preferences[user_id]["period"] = period

def get_user_language(user_id: int) -> Optional[str]:
    """Get user's last selected language"""
    return user_preferences.get(user_id, {}).get("language")

def set_user_language(user_id: int, language: str):
    """Set user's selected language"""
    if user_id not in user_preferences:
        user_preferences[user_id] = {}
    user_preferences[user_id]["language"] = language