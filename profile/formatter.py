# profile/formatter.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.formatting import (
    add_admin_context, format_admin_badge, format_tip_text,
    format_loading_text, format_error_text, extract_username_from_action
)


class ProfileFormatter:
    """Handles text formatting and keyboard generation for profile features"""

    # ==================== ERROR MESSAGES ====================
    
    def format_user_not_found(self, username: str, is_admin: bool = False) -> str:
        """Format user not found error message"""
        content = (
            f"👤 **User Search**\n\n"
            f"❌ **User Not Found**\n\n"
            f"User `{username}` not found on GitHub.\n\n"
            f"**Possible reasons:**\n"
            f"• Username doesn't exist\n"
            f"• Account was deleted\n"
            f"• Typo in username\n\n"
            f"{format_tip_text('Double-check the username spelling!')}"
        )
        
        return add_admin_context(content, username) if is_admin else content
    
    def format_search_error(self, username: str, is_admin: bool = False) -> str:
        """Format search error message"""
        content = (
            f"👤 **{username}'s Profile**\n\n"
            f"❌ **Search Error**\n\n"
            f"Unable to search for user profile.\n\n"
            f"**Possible causes:**\n"
            f"• Network connection issues\n"
            f"• GitHub API temporarily unavailable\n"
            f"• Rate limiting\n\n"
            f"{format_tip_text('Wait a moment and try again!')}"
        )
        
        return add_admin_context(content, username) if is_admin else content
    
    def format_callback_error(self, username: str, error_type: str = "Action Error", is_admin: bool = False) -> str:
        """Format callback error message"""
        content = (
            f"👤 **{username}'s Profile**\n\n"
            f"❌ **{error_type}**\n\n"
            f"Something went wrong with this action.\n\n"
            f"{format_tip_text('Try the action again or go back to profile!')}"
        )
        
        return add_admin_context(content, username) if is_admin else content
    
    def format_session_lost(self, is_admin: bool = False) -> str:
        """Format session lost error message"""
        content = (
            f"👤 **User Profile**\n\n"
            f"❌ **Session Expired**\n\n"
            f"Your session has expired or profile data was lost.\n\n"
            f"{format_tip_text('Search for the user again!')}"
        )
        
        return content  # No username available for admin context

    # ==================== AVATAR MESSAGES ====================
    
    def format_avatar_display(self, username: str, is_admin: bool = False) -> str:
        """Format avatar display caption"""
        content = (
            f"👤 **{username}'s GitHub Avatar**\n\n"
            f"📸 Profile picture displayed!\n\n"
            f"{format_tip_text('Use buttons below to navigate!')}"
        )
        
        return add_admin_context(content, username) if is_admin else content
    
    def format_avatar_refreshed(self, username: str, is_admin: bool = False) -> str:
        """Format avatar refreshed caption"""
        content = (
            f"👤 **{username}'s GitHub Avatar**\n\n"
            f"📸 Avatar refreshed!\n\n"
            f"{format_tip_text('Avatar updated successfully!')}"
        )
        
        return add_admin_context(content, username) if is_admin else content
    
    def format_avatar_loading(self, original_caption: str, action: str) -> str:
        """Format avatar loading caption"""
        return f"{original_caption}\n\n{format_loading_text(action)}"
    
    def format_avatar_error(self, original_caption: str, error_msg: str) -> str:
        """Format avatar error caption"""
        return f"{original_caption}\n\n{format_error_text(error_msg)}"

    # ==================== PROFILE MESSAGES ====================
    
    def format_search_tip(self, username: str, is_admin: bool = False) -> str:
        """Format initial search tip message"""
        admin_badge = f" {format_admin_badge()}" if is_admin else ""
        return f"👤 **{username}'s Profile{admin_badge}**\n\n{format_tip_text('Searching for user...')}"
    
    def format_profile_loading(self, username: str, is_admin: bool = False) -> str:
        """Format profile loading message"""
        admin_badge = f" {format_admin_badge()}" if is_admin else ""
        return f"👤 **{username}'s Profile{admin_badge}**"
    
    def format_profile_restored(self, username: str, is_admin: bool = False) -> str:
        """Format profile restoration message"""
        admin_badge = f" {format_admin_badge()}" if is_admin else ""
        return f"👤 **{username}'s Profile{admin_badge}**\n\n{format_loading_text('Restoring profile')}"

    # ==================== KEYBOARD GENERATION ====================
    
    def get_user_not_found_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for user not found error"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        ])
    
    def get_search_error_keyboard(self, username: str) -> InlineKeyboardMarkup:
        """Get keyboard for search error"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Retry", callback_data=f"refresh_user_{username}"),
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ])
    
    def get_callback_error_keyboard(self, action: str) -> InlineKeyboardMarkup:
        """Get keyboard for callback error"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Try Again", callback_data=action),
                InlineKeyboardButton("🏠 Back to Profile", callback_data="back_to_profile")
            ],
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        ])
    
    def get_session_lost_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for session lost error"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        ])
    
    def get_avatar_keyboard(self, username: str) -> InlineKeyboardMarkup:
        """Get avatar navigation keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🏠 Back to Profile", callback_data="back_to_profile"),
                InlineKeyboardButton("🔄 Refresh Avatar", callback_data=f"refresh_avatar_{username}")
            ],
            [
                InlineKeyboardButton("📂 Repositories", callback_data=f"user_repos_{username}"),
                InlineKeyboardButton("⭐ Starred", callback_data=f"user_starred_{username}")
            ],
            [
                InlineKeyboardButton("👥 Followers", callback_data=f"user_followers_{username}"),
                InlineKeyboardButton("👤 Following", callback_data=f"user_following_{username}")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ])


# Create formatter instance
profile_formatter = ProfileFormatter()