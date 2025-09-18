# help.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from templates import get_help_message, get_error_message
from utils.loading import with_loading

logger = logging.getLogger(__name__)

@with_loading
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - single help page"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
    ])

    help_text = get_help_message()

    try:
        # Use the loading message from context
        message = context.user_data.get('_loading_message')
        if message:
            await message.edit_text(
                help_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        else:
            # Fallback (shouldn't happen with decorator)
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.edit_text(
                    help_text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    help_text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        error_text = get_error_message("Help", str(e))
        
        message = context.user_data.get('_loading_message')
        if message:
            await message.edit_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )