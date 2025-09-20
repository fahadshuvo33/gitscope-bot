# start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import os

from templates import get_welcome_message, get_error_message
from admin import is_admin_telegram
from utils.db_logger import log_activity
from utils.loading import with_loading

logger = logging.getLogger(__name__)

@with_loading
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
            InlineKeyboardButton("🆘 Help", callback_data="help_menu")
        ],
        [
            InlineKeyboardButton("💻 Developer", callback_data="developer_info"),
            InlineKeyboardButton("ℹ️ About", callback_data="about_info")
        ]
    ]
    
    # Add logs button for admin
    if user.username and is_admin_telegram(user.username):
        buttons.append([InlineKeyboardButton("📋 Logs", callback_data="show_logs")])
    
    keyboard = InlineKeyboardMarkup(buttons)

    try:
        # Get welcome text
        welcome_text = get_welcome_message(username=user_name)

        # Use the loading message from context
        message = context.user_data.get('_loading_message')
        if message:
            await message.edit_text(
                welcome_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        else:
            # Fallback if no loading message (shouldn't happen with decorator)
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.edit_text(
                    welcome_text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    welcome_text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        message = context.user_data.get('_loading_message')
        error_text = get_error_message("Start", str(e))
        
        if message:
            await message.edit_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )


