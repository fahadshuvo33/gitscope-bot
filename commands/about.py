# about.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import asyncio
from templates import get_about_info, get_error_message
from utils.loading import with_loading

logger = logging.getLogger(__name__)

# Method 1: Using the simplified decorator
@with_loading  # Animation runs for 1.5 seconds, then your function runs
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
    ])

    try:
        # Get the about information
        about_text = get_about_info()
        
        # Get the loading message from context
        message = context.user_data.get('_loading_message')
        
        if message:
            # The animation has already stopped, just update
            await message.edit_text(
                about_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )

    except Exception as e:
        logger.error(f"Error in about command: {e}", exc_info=True)
        
        message = context.user_data.get('_loading_message')
        if message:
            error_text = get_error_message("About", str(e))
            await message.edit_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )

