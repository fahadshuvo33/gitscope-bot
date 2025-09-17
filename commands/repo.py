# commands/repository.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from templates import get_repo_message, get_error_message
from utils.manager import utils
from utils.db_logger import log_activity

logger = logging.getLogger(__name__)

async def handle_repository(update: Update, repo_owner: str, repo_name: str, is_admin: bool = False):
    """Handle GitHub repository requests"""
    user = update.effective_user
    user_id = user.username or f"user_{user.id}"
    repo_full_name = f"{repo_owner}/{repo_name}"
    
    log_activity("INFO", f"Repository request: {repo_full_name}", user_id=user_id, command="repository")
    
    loading_msg = await update.message.reply_text(
        f"📚 Loading repository: {repo_full_name}...",
        parse_mode="Markdown"
    )
    
    try:
        repo_data = await utils.github_api.get_repository_info(repo_full_name)
        
        if not repo_data:
            await loading_msg.edit_text(
                f"❌ Repository '{repo_full_name}' not found",
                parse_mode="Markdown"
            )
            return
        
        repo_text = get_repo_message(
            name=repo_data.get('name', ''),
            full_name=repo_data.get('full_name', repo_full_name),
            description=repo_data.get('description', ''),
            language=repo_data.get('language', 'N/A'),
            stars=repo_data.get('stargazers_count', 0),
            forks=repo_data.get('forks_count', 0),
            issues=repo_data.get('open_issues_count', 0),
            is_admin=is_admin
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        await loading_msg.edit_text(
            repo_text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error loading repository {repo_full_name}: {e}", exc_info=True)
        error_text = get_error_message("Repository", str(e))
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        await loading_msg.edit_text(error_text, reply_markup=keyboard)