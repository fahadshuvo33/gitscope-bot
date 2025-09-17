# commands/profile.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from templates import get_profile_message, get_error_message
from utils.manager import utils
from utils.db_logger import log_activity

logger = logging.getLogger(__name__)

async def handle_profile(update: Update, username: str, is_admin: bool = False):
    """Handle GitHub profile requests"""
    user = update.effective_user
    user_id = user.username or f"user_{user.id}"
    
    log_activity("INFO", f"Profile request: {username}", user_id=user_id, command="profile")
    
    loading_msg = await update.message.reply_text(
        f"👤 Loading profile: {username}...",
        parse_mode="Markdown"
    )
    
    try:
        profile_data = await utils.github_api.get_user_profile(username)
        
        if not profile_data:
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
        
        await loading_msg.edit_text(
            profile_text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error loading profile {username}: {e}", exc_info=True)
        error_text = get_error_message("Profile", str(e))
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        await loading_msg.edit_text(error_text, reply_markup=keyboard)