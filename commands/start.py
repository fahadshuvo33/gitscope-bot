from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import os

from templates import get_welcome_message, get_error_message
from admin import is_admin
from utils.db_logger import log_activity
# from utils.loading import withLoading

logger = logging.getLogger(__name__)

# @withLoading
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - simplified"""
    
    user = update.effective_user
    user_name = user.first_name or "User"
    user_id = user.username or f"user_{user.id}"
    
    log_activity("INFO", "Start command accessed", user_id=user_id, command="start")

    # Create keyboard
    buttons = [
        [
            InlineKeyboardButton("📈 Trending", callback_data="trending_menu"),
            InlineKeyboardButton("🇭🇪 Help", callback_data="help_menu")
        ],
        [
            InlineKeyboardButton("💻 Developer", callback_data="developer_info"),
            InlineKeyboardButton("ℹ️ About", callback_data="about_info")
        ]
    ]
    
    # Add logs button for admin
    if user.username and is_admin(user.username):
        buttons.append([InlineKeyboardButton("📋 Logs", callback_data="show_logs")])
    
    keyboard = InlineKeyboardMarkup(buttons)

    try:
        # Get welcome text directly
        welcome_text = get_welcome_message(username=user_name)

        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                welcome_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                welcome_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        try:
            error_text = get_error_message("Start", str(e))
            if update.callback_query:
                await update.callback_query.edit_message_text(error_text, reply_markup=keyboard)
            else:
                await update.message.reply_text(error_text, reply_markup=keyboard)
        except:
            pass
        
# @withLoading
async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start-related callback queries"""
    
    if not update.callback_query:
        return
    
    query = update.callback_query
    data = query.data
    
    # Handle different start menu options
    if data == "help_menu":
        from .help import help_command
        await help_command(update, context)
    elif data == "trending_menu":
        from .trending import trending_command
        await trending_command(update, context)
