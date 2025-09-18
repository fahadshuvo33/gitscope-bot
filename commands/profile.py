# profile.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from templates import get_profile_message, get_error_message
from utils.manager import utils
from utils.db_logger import log_activity
from utils.loading import with_loading

logger = logging.getLogger(__name__)

@with_loading("👤 Loading profile")
async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str, is_admin: bool = False):
    """Handle GitHub profile requests"""
    user = update.effective_user
    user_id = user.username or f"user_{user.id}"
    
    log_activity("INFO", f"Profile request: {username}", user_id=user_id, command="profile")
    
    # Get loading message from context
    loading_msg = context.user_data.get('_loading_message')
    
    try:
        profile_data = await utils.github_api.get_user_profile(username)
        
        if not profile_data:
            if loading_msg:
                await loading_msg.edit_text(
                    f"❌ User '{username}' not found",
                    parse_mode="Markdown"
                )
            return
        
        profile_text = get_profile_message(
            name=profile_data.get('name', username),
            login=profile_data.get('login', username),
            bio=profile_data.get('bio', ''),
            location=profile_data.get('location', ''),
            company=profile_data.get('company', ''),
            followers=profile_data.get('followers', 0),
            following=profile_data.get('following', 0),
            public_repos=profile_data.get('public_repos', 0),
            is_admin=is_admin
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        if loading_msg:
            await loading_msg.edit_text(
                profile_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        
    except Exception as e:
        logger.error(f"Error loading profile {username}: {e}", exc_info=True)
        error_text = get_error_message("Profile", str(e))
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        if loading_msg:
            await loading_msg.edit_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )